from pg_orgtree import *


def get_chdb():
    return alchemy_engines["ch"]


def dfs(OrgTreeNode_id: int, dct_Sensors: dict, pg: Session = Depends(get_pgdb)):
    db_OrgTreeNode = pg.get(OrgTreeNode, OrgTreeNode_id)
    if (db_OrgTreeNode.type == "sensor"):
        Sensor_id = db_OrgTreeNode.object_id
        db_Sensor = pg.get(Sensor, Sensor_id)
        db_SensorType = pg.get(SensorType, db_Sensor.type_id)
        dct_Sensors[Sensor_id] = {
            "ch_id": db_Sensor.ch_id,
            "freq": db_SensorType.freq,
            "dim": db_SensorType.dim
        }
    _, adj = db_get_adj(OrgTreeNode_id, pg)
    for v in adj:
        dfs(v[0], dct_Sensors, pg)


def get_col_name(Sensor_id, ind):
    return "Sensor_" + str(Sensor_id) + "_value_" + str(ind + 1)


def get_table_name(id: int):
    return "CH_Sensor_" + str(id)


DT_1S = timedelta(seconds=1)
RFC3339_FORMAT = "%Y-%m-%dT%H:%M:%S.%fZ"


def parse_interval(interval):
    if (interval):
        l, r = interval[0] - DT_1S, interval[1] + DT_1S
        return " WHERE t BETWEEN \'" + str(l) + "\' AND \'" + str(r) + "\'"
    else:
        return ""


# Single table implementation


def single_post_ch_data(interval, dct_Sensors: dict, ch=Depends(get_chdb)):
    single_create_table(dct_Sensors, ch)
    single_gen_data(dct_Sensors, interval, ch)


def single_create_table(dct_Sensors: dict, ch=Depends(get_chdb)):
    s = "CREATE TABLE IF NOT EXISTS Sensors_Data ( "
    s += "t DateTime64(6)"
    for x, y in dct_Sensors.items():
        for i in range(y["dim"]):
            s += ", " + get_col_name(x, i) + " Float64"
    s += ") ENGINE = MergeTree"
    s += " ORDER BY t"
    ch.execute(s)


def single_gen_row(tl, ts, i, types):
    t = ts[i]
    yield t
    for y in types.values():
        elapsed = (t - tl).total_seconds()
        ind = int(elapsed * y["freq"])
        for j in range(y["dim"]):
            yield (ind * y["dim"] + j) / 10.0


def single_gen_data(dct_Sensors: dict, interval, ch=Depends(get_chdb)):
    tl, tr = interval
    seconds = int((tr - tl).total_seconds())
    ts = []
    for y in dct_Sensors.values():
        dt = 1.0 / y["freq"]
        for i in range(y["freq"] * seconds):
            ts.append(tl + timedelta(seconds=i * dt))
    ts = np.unique(ts)
    n = ts.shape[0]
    a = [single_gen_row(tl, ts, i, dct_Sensors)
         for i in range(n)]
    ch.execute("INSERT INTO Sensors_Data VALUES", a)


def single_get_ch_data(fname: str, interval, dctSensors: dict, ch=Depends(get_chdb)):
    cols = ["Time, ms"]
    q = "SELECT t"
    for x, y in dctSensors.items():
        for i in range(y["dim"]):
            col_name = get_col_name(x, i)
            cols.append(col_name)
            q += ", " + col_name
    q += " FROM Sensors_Data"
    q += parse_interval(interval)
    f = open(fname, "w")
    fcsv = csv.writer(f)
    fcsv.writerow(cols)
    res = ch.execute(q)
    for row in res:
        fcsv.writerow(row)
    f.close()

# Multiple tables implementation


def multi_create_table(id: int, db_SensorType: SensorType, db=Depends(get_chdb)):
    s, t = "", get_table_name(id)
    s += "CREATE TABLE IF NOT EXISTS " + t + " ( "
    s += "t DateTime64(6)"
    for i in range(db_SensorType.dim):
        s += ", value_" + str(i) + " Float64"
    s += ") ENGINE = MergeTree"
    s += " ORDER BY t"
    db.execute(s)


def multi_post_ch_data(interval, dct_Sensors: dict, ch=Depends(get_chdb)):
    multi_gen_data(dct_Sensors, interval, ch)


def multi_gen_row(tl, dt, ind, dim):
    yield tl + timedelta(seconds=ind * dt)
    for j in range(dim):
        yield (ind * dim + j) / 10.0


def multi_gen_data(dct_Sensors: dict, interval, ch=Depends(get_chdb)):
    tl, tr = interval
    seconds = int((tr - tl).total_seconds())
    for y in dct_Sensors.values():
        dt = 1.0 / y["freq"]
        a = [multi_gen_row(tl, dt, i, y["dim"])
             for i in range(y["freq"] * seconds)]
        ch.execute("INSERT INTO " +
                   get_table_name(y["ch_id"]) + " VALUES", a)


def get_sensor_data(Sensor_id: int, ch=Depends(get_chdb), interval=None):
    q = "SELECT * FROM " + get_table_name(Sensor_id)
    q += parse_interval(interval)
    return ch.execute(q)


def multi_get_ch_data(fname: str, interval, dctSensors: dict, ch=Depends(get_chdb)):
    cols = ["Time, ms"]
    ts = []
    m = 0
    n_sens = len(dctSensors.keys())
    cursors = []
    tinterval = parse_interval(interval)
    for x, y in dctSensors.items():
        m += y["dim"]
        for i in range(y["dim"]):
            col_name = get_col_name(x, i)
            cols.append(col_name)
        cursors.append(ch.execute("SELECT * FROM " +
                                  get_table_name(y["ch_id"]) + tinterval))
        rep = ch.execute("SELECT t FROM " +
                         get_table_name(y["ch_id"]) + tinterval)
        for elem in rep:
            ts.append(elem[0])
    ts = np.unique(ts)
    row = [0.0 for _ in range(m + 1)]
    f = open(fname, "w")
    fcsv = csv.writer(f)
    fcsv.writerow(cols)
    ptrs = [cursors[i].fetchone() for i in range(n_sens)]
    ptrs_next = [cursors[i].fetchone() for i in range(n_sens)]
    end_of_it = [False for _ in range(n_sens)]
    for i in range(ts.shape[0]):
        good = True
        for ii in range(n_sens):
            if (ptrs[ii][0] > ts[i]):
                good = False
                break
            while (not end_of_it[ii] and ptrs_next[ii][0] <= ts[i]):
                ptrs[ii] = ptrs_next[ii]
                ptrs_next[ii] = cursors[ii].fetchone()
                if (ptrs_next[ii] == None):
                    end_of_it[ii] = True
        if (not good):
            continue
        j = 1
        row[0] = ts[i]
        for ii in range(n_sens):
            for elem in ptrs[ii][1:]:
                row[j] = elem
                j += 1
        fcsv.writerow(row)
    f.close()

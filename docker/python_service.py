import os
from fastapi import Depends, FastAPI, HTTPException, Request
from sqlalchemy import create_engine, Column, MetaData, BigInteger, Text, Boolean, Date, exc
from sqlalchemy.sql import text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import Session
from fastapi.responses import FileResponse
from datetime import date, datetime, timedelta
from io import StringIO
from fastapi.middleware.cors import CORSMiddleware

from clickhouse_sqlalchemy import Table, make_session, get_declarative_base, types, engines

import graphviz
import numpy as np
import pandas as pd

# Start SQL Alchemy
alchemy_engines = {
    "pg": create_engine(
        "postgresql+psycopg2://pguser:pguser@localhost:25500/pgdb", echo=True),
    "ch": create_engine("clickhouse+native://chuser:chuser@localhost:25501/chdb", echo=True)
}

metadatas = {
    "ch": MetaData(bind=alchemy_engines["ch"])
}

bases = {
    "pg": declarative_base(),
    "ch": get_declarative_base(metadata=MetaData(bind=alchemy_engines["ch"]))
}


class OrgTreeEdge(bases["pg"]):
    __tablename__ = "OrgTreeEdges"
    id = Column(BigInteger, primary_key=True, index=True)
    id_u = Column(BigInteger)
    id_v = Column(BigInteger)
    parent = Column(Boolean)
    date = Column(Date)


class OrgTreeNode(bases["pg"]):
    __tablename__ = "OrgTreeNodes"
    id = Column(BigInteger, primary_key=True, index=True)
    type = Column(Text)
    object_id = Column(BigInteger)
    date = Column(Date)


class OrgUnit(bases["pg"]):
    __tablename__ = "OrgUnits"
    id = Column(BigInteger, primary_key=True, index=True)
    name = Column(Text)
    type = Column(Text)
    json = Column(Text)
    date = Column(Date)


class Sensor(bases["pg"]):
    __tablename__ = "Sensors"
    id = Column(BigInteger, primary_key=True, index=True)
    type_id = Column(BigInteger)
    ch_id = Column(BigInteger)
    date = Column(Date)


class SensorType(bases["pg"]):
    __tablename__ = "SensorTypes"
    id = Column(BigInteger, primary_key=True, index=True)
    freq = Column(BigInteger)
    dim = Column(BigInteger)
    info = Column(Text)


bases["pg"].metadata.create_all(bind=alchemy_engines["pg"])


def get_chdb():
    return alchemy_engines["ch"]


def get_pgdb():
    Session = sessionmaker(
        autocommit=False, autoflush=False, bind=alchemy_engines["pg"])
    db = Session()
    try:
        yield db
    finally:
        db.close()


# Start FastAPI
app = FastAPI()

# Cross-Origin Resource Sharing
origins = [
    "http://localhost",
    "http://localhost:8080"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def OrgTreeNode_to_schema(db_OrgTreeNode: OrgTreeNode):
    return {
        "id": db_OrgTreeNode.id,
        "type": db_OrgTreeNode.type,
        "object_id": db_OrgTreeNode.object_id,
        "date": db_OrgTreeNode.date
    }


@app.get("/OrgTreeNodes/{OrgTreeNode_id}")
async def get_OrgTreeNode(OrgTreeNode_id: int, db: Session = Depends(get_pgdb)):
    db_OrgTreeNode = db.get(OrgTreeNode, OrgTreeNode_id)
    if db_OrgTreeNode is None:
        raise HTTPException(status_code=404, detail="OrgTreeNode not found")
    return OrgTreeNode_to_schema(db_OrgTreeNode)


def db_get_adj(u: int, db: Session = Depends(get_pgdb)):
    parent = db.execute(text(
        "SELECT id_v FROM \"OrgTreeEdges\" WHERE id_u = " + str(u) + " AND parent = true AND date is null")).fetchone()
    lst_adj = db.execute(text(
        "SELECT id_v FROM \"OrgTreeEdges\" WHERE id_u = " + str(u) + " AND parent = false AND date is null")).all()
    return parent, lst_adj


def delete_node(OrgTreeNode_id: int, db: Session = Depends(get_pgdb)):
    db_OrgTreeNode = db.get(OrgTreeNode, OrgTreeNode_id)
    if db_OrgTreeNode is None:
        raise HTTPException(status_code=404, detail="OrgTreeNode not found")
    if (db_OrgTreeNode.date != None):
        return OrgTreeNode_to_schema(db_OrgTreeNode)
    u = db_OrgTreeNode.id
    parent, adj = db_get_adj(u, db)
    if (parent != None):
        delete_edge(u, parent[0], db)
    db_OrgTreeNode.date = date.today()
    db.commit()
    for v in adj:
        delete_node(v[0], db)
    return OrgTreeNode_to_schema(db_OrgTreeNode)


@ app.delete("/OrgTreeNodes/{OrgTreeNode_id}")
async def delete_OrgTreeNode(OrgTreeNode_id: int, db: Session = Depends(get_pgdb)):
    try:
        res = delete_node(OrgTreeNode_id, db)
        return res
    except BaseException as ex:
        raise ex


def check_OrgUnit(OrgUnit_id: int, db: Session = Depends(get_pgdb)):
    db_OrgUnit = db.get(OrgUnit, OrgUnit_id)
    return False if db_OrgUnit == None else True


def check_Sensor(Sensor_id: int, db: Session = Depends(get_pgdb)):
    db_Sensor = db.get(Sensor, Sensor_id)
    return False if db_Sensor == None else True


@ app.post("/OrgTreeNodes")
async def add_OrgTreeNode(request: Request, db: Session = Depends(get_pgdb)):
    param_json = await request.json()
    node_type = param_json["type"]
    obj_id = param_json["object_id"]
    if (node_type == "sensor"):
        if not (check_Sensor(obj_id, db)):
            raise HTTPException(
                status_code=404, detail="Sensor " + str(obj_id) + " not found")
    elif (node_type == "orgunit"):
        if not (check_OrgUnit(obj_id, db)):
            raise HTTPException(
                status_code=404, detail="Org unit " + str(obj_id) + " not found")
    else:
        raise HTTPException(
            status_code=500, detail="Invalid type")
    db_OrgTreeNode = OrgTreeNode(type=node_type, object_id=obj_id)
    db.add(db_OrgTreeNode)
    db.commit()
    return OrgTreeNode_to_schema(db_OrgTreeNode)


def check_OrgTreeNode(OrgTreeNode_id: int, db: Session = Depends(get_pgdb)):
    db_OrgTreeNode = db.get(OrgTreeNode, OrgTreeNode_id)
    return False if db_OrgTreeNode == None or db_OrgTreeNode.date != None else True


def OrgTreeEdge_to_schema(db_OrgTreeEdge: OrgTreeEdge):
    return {
        "id": db_OrgTreeEdge.id,
        "id_u": db_OrgTreeEdge.id_u,
        "id_v": db_OrgTreeEdge.id_v,
        "parent": db_OrgTreeEdge.parent,
        "date": db_OrgTreeEdge.date
    }


@ app.post("/OrgTreeEdges")
async def add_OrgTreeEdge(request: Request, db: Session = Depends(get_pgdb)):
    param_json = await request.json()
    u = param_json["id_u"]
    v = param_json["id_v"]
    if (u == v):
        raise HTTPException(
            status_code=500, detail="Can't add self edge")
    if not (check_OrgTreeNode(u, db)):
        raise HTTPException(
            status_code=404, detail="OrgTreeNode " + str(u) + " not found or deleted")
    if not (check_OrgTreeNode(v, db)):
        raise HTTPException(
            status_code=404, detail="OrgTreeNode " + str(v) + " not found or delete")
    db_OrgTreeEdge = db_get_edge(u, v, db)
    if (db_OrgTreeEdge != None):
        raise HTTPException(
            status_code=500, detail="Edges already exist")
    db_OrgTreeEdge_uv = OrgTreeEdge(id_u=u, id_v=v, parent=False)
    db.add(db_OrgTreeEdge_uv)
    db_OrgTreeEdge_vu = OrgTreeEdge(id_u=v, id_v=u, parent=True)
    db.add(db_OrgTreeEdge_vu)
    db.commit()
    return OrgTreeEdge_to_schema(db_OrgTreeEdge_uv)


def db_get_edge(u: int, v: int, db: Session = Depends(get_pgdb)):
    return db.execute(text(
        "SELECT * FROM \"OrgTreeEdges\" WHERE id_u = " + str(u) + " AND id_v = " + str(v))).fetchone()


def inv_edge_id(id: int):
    return ((id - 1) ^ 1) + 1


def delete_edge(u: int, v: int, db: Session = Depends(get_pgdb)):
    db_OrgTreeEdge = db_get_edge(u, v, db)
    if db_OrgTreeEdge is None:
        raise HTTPException(status_code=404, detail="OrgTreeEdge not found")
    db_OrgTreeEdge_uv = db.get(OrgTreeEdge, db_OrgTreeEdge.id)
    db_OrgTreeEdge_vu = db.get(OrgTreeEdge, inv_edge_id(db_OrgTreeEdge.id))
    if (db_OrgTreeEdge_uv.id_u != db_OrgTreeEdge_vu.id_v or db_OrgTreeEdge_uv.id_v != db_OrgTreeEdge_vu.id_u):
        raise HTTPException(status_code=500, detail="FAIL, incorrect edges!")
    if (db_OrgTreeEdge_uv.date == None):
        db_OrgTreeEdge_uv.date = date.today()
        db_OrgTreeEdge_vu.date = date.today()
    db.commit()
    return OrgTreeEdge_to_schema(db_OrgTreeEdge_uv)


@ app.delete("/OrgTreeEdges")
async def delete_OrgTreeEdge(request: Request, db: Session = Depends(get_pgdb)):
    param_json = await request.json()
    try:
        res = delete_edge(param_json["id_u"], param_json["id_v"], db)
        return res
    except BaseException as ex:
        raise ex


def Sensor_to_schema(db_Sensor: Sensor):
    return {
        "id": db_Sensor.id,
        "type_id": db_Sensor.type_id,
        "ch_id": db_Sensor.ch_id,
        "date": db_Sensor.date
    }


def get_SensorType(SensorType_id: int, db: Session = Depends(get_pgdb)):
    return db.get(SensorType, SensorType_id)


def get_table_name(id: int):
    return "CH_Sensor_" + str(id)


N_ROWS_TO_GEN = 100
DT_1S = timedelta(seconds=1)
RFC3339_FORMAT = "%Y-%m-%dT%H:%M:%S.%fZ"


def arr_to_string(a):
    out = StringIO()
    print(a, file=out, end="")
    res = out.getvalue()
    out.close()
    return res[1:len(res) - 1]


def create_new_ch_table(id: int, freq: int, n_params: int, db=Depends(get_chdb)):
    s, t = "", get_table_name(id)
    s += "CREATE TABLE IF NOT EXISTS " + t + " ( "
    s += "t DateTime64(6)"
    for i in range(n_params):
        s += ", value_" + str(i) + " Float64"
    s += ") ENGINE = MergeTree"
    s += " ORDER BY t"
    db.execute(s)
    arr = []
    now = datetime.strptime("2023-02-20T10:30:40.123Z", RFC3339_FORMAT)
    delta = 1.0 / freq
    a = [0.0 for _ in range(n_params + 1)]
    for i in range(freq * N_ROWS_TO_GEN):
        for j in range(n_params):
            a[j + 1] = (i * n_params + j) / 10.0
        a[0] = (now + timedelta(seconds=i * delta)).timestamp()
        arr.append(tuple(a))
    s = ""
    s += "INSERT INTO " + t + " VALUES " + arr_to_string(arr)
    db.execute(s)


@ app.post("/Sensors")
async def add_Sensor(request: Request, db: Session = Depends(get_pgdb), ch=Depends(get_chdb)):
    param_json = await request.json()
    SensorType_id = param_json["type_id"]
    db_SensorType = get_SensorType(SensorType_id, db)
    if (db_SensorType == None):
        raise HTTPException(status_code=500, detail="Sensor type not found")
    cnt_ch_tables = len(ch.execute("SHOW TABLES").fetchall()) + 1
    create_new_ch_table(cnt_ch_tables, db_SensorType.freq,
                        db_SensorType.dim, ch)
    db_Sensor = Sensor(type_id=SensorType_id, ch_id=cnt_ch_tables)
    db.add(db_Sensor)
    db.commit()
    return Sensor_to_schema(db_Sensor)


@ app.get("/Sensors/{Sensor_id}")
async def get_Sensor(Sensor_id: int, db: Session = Depends(get_pgdb)):
    db_Sensor = db.get(Sensor, Sensor_id)
    if db_Sensor is None:
        raise HTTPException(status_code=404, detail="Sensor not found")
    return Sensor_to_schema(db_Sensor)


def get_sensor_data(id: int, ch=Depends(get_chdb), interval=None):
    q = "SELECT * FROM " + get_table_name(id)
    if (interval):
        l, r = interval[0] - DT_1S, interval[1] + DT_1S
        q += " WHERE t BETWEEN \'" + str(l) + "\' AND \'" + str(r) + "\'"
    return ch.execute(q).fetchall()


def dfs(OrgTreeNode_id: int, data, cols, db: Session = Depends(get_pgdb), ch=Depends(get_chdb), interval=None):
    db_OrgTreeNode = db.get(OrgTreeNode, OrgTreeNode_id)
    _, adj = db_get_adj(OrgTreeNode_id, db)
    if (db_OrgTreeNode.type == "sensor"):
        Sensor_id = db_OrgTreeNode.object_id
        s = "Sensor" + str(Sensor_id)
        data[s] = get_sensor_data(Sensor_id, ch, interval)
        db_Sensor = db.get(Sensor, Sensor_id)
        db_SensorType = db.get(SensorType, db_Sensor.type_id)
        dim = db_SensorType.dim
        for i in range(1, dim + 1):
            cols.append("Sensor " + str(Sensor_id) + ", value " + str(i))
    for v in adj:
        dfs(v[0], data, cols, db, ch, interval)


def convert_ch_to_np(data):
    if (not data):
        raise HTTPException(status_code=500, detail="No data")
    for y in data.values():
        if (not y):
            raise HTTPException(status_code=500, detail="No data")
    print("-" * 10, " DEBUG BEGIN ", "-" * 10)
    keys_sensors = list(data.keys())
    sz_sensors = list(len(y) for y in data.values())
    dims = list(len(y[0]) - 1 for y in data.values())
    n = sum(len(data[elem]) for elem in data.keys())
    t = np.empty(n, dtype=np.float64)
    i, m, n_sens = 0, sum(dims), len(dims)
    t_sensors = list()
    for y in data.values():
        t_cur = np.empty(len(y), dtype=np.float64)
        j = 0
        for val in y:
            t[i] = val[0].timestamp()
            t_cur[j] = t[i]
            i += 1
            j += 1
        t_sensors.append(t_cur)
    t = np.unique(t)
    n = t.shape[0]
    res = np.empty((n, m), dtype=np.float64)
    print("dims = ", res.shape)
    ptr = [0 for _ in range(n_sens)]
    ind_all_good = -1
    for i in range(n):
        good = True
        for j in range(n_sens):
            while (ptr[j] < sz_sensors[j] and t_sensors[j][ptr[j]] < t[i]):
                ptr[j] += 1
            if (ptr[j] == 0):
                good = False
                break
        if (not good):
            continue
        elif (ind_all_good == -1):
            ind_all_good = i
        j = 0
        for ii in range(n_sens):
            y = data[keys_sensors[ii]]
            ind = ptr[ii] - 1
            for jj in range(dims[ii]):
                res[i][j] = np.float64(y[ind][jj + 1])
                j += 1
    res = np.concatenate((np.array([t]).T, res), axis=1)
    res = np.delete(res, obj=slice(0, ind_all_good), axis=0)
    # for el in res:
    #     print(el)
    # for y in data.values():
    #     print()
    #     for val in y:
    #         print(val[0], val[0].timestamp(), val[1:])
    print("-" * 10, " DEBUG END ", "-" * 10)
    return res


@ app.get("/OrgTreeNodes/{OrgTreeNode_id}/CH_Data")
async def get_OrgTreeNode(OrgTreeNode_id: int, time_begin, time_end, db: Session = Depends(get_pgdb), ch=Depends(get_chdb)):
    interval = (datetime.strptime(
        time_begin, RFC3339_FORMAT), datetime.strptime(time_end, RFC3339_FORMAT))
    db_OrgTreeNode = db.get(OrgTreeNode, OrgTreeNode_id)
    if db_OrgTreeNode is None:
        raise HTTPException(status_code=404,
                            detail="OrgTreeNode not found")
    try:
        data = dict()
        cols = ["Time, ms"]
        dfs(OrgTreeNode_id, data, cols, db, ch, interval)
        df = pd.DataFrame(convert_ch_to_np(data), columns=cols)
        df.to_csv("rep.csv")
        return FileResponse("./rep.csv")
    except BaseException as ex:
        raise ex


@ app.put("/Sensors/{Sensor_id}")
async def edit_Sensor(Sensor_id: int, request: Request, db: Session = Depends(get_pgdb), ch=Depends(get_chdb)):
    db_Sensor = db.get(Sensor, Sensor_id)
    if db_Sensor is None:
        raise HTTPException(status_code=404, detail="Sensor not found")
    param_json = await request.json()
    SensorType_id = param_json["type_id"]
    db_SensorType = get_SensorType(SensorType_id, db)
    if (db_SensorType == None):
        raise HTTPException(status_code=500,
                            detail="Sensor type not found")
    cnt_ch_tables = len(ch.execute("SHOW TABLES").fetchall()) + 1
    create_new_ch_table(cnt_ch_tables, db_SensorType.freq,
                        db_SensorType.dim, ch)
    db_Sensor.type_id = SensorType_id
    db_Sensor.ch_id = cnt_ch_tables
    db.commit()
    return Sensor_to_schema(db_Sensor)


@ app.delete("/Sensors/{Sensor_id}")
async def delete_Sensor(Sensor_id: int, db: Session = Depends(get_pgdb)):
    db_Sensor = db.get(Sensor, Sensor_id)
    if db_Sensor is None:
        raise HTTPException(status_code=404, detail="Sensor not found")
    db_Sensor.date = date.today()
    db.commit()
    return Sensor_to_schema(db_Sensor)


def SensorType_to_schema(db_SensorType: SensorType):
    return {
        "id": db_SensorType.id,
        "freq": db_SensorType.freq,
        "dim": db_SensorType.dim,
        "info": db_SensorType.info
    }


@ app.post("/SensorTypes")
async def add_SensorType(request: Request, db: Session = Depends(get_pgdb)):
    params = await request.json()
    db_SensorType = SensorType(freq=params["freq"],
                               dim=params["dim"],
                               info=params["info"])
    db.add(db_SensorType)
    db.commit()
    return SensorType_to_schema(db_SensorType)


def OrgUnit_to_schema(db_OrgUnit: OrgUnit):
    return {
        "id": db_OrgUnit.id,
        "name": db_OrgUnit.name,
        "type": db_OrgUnit.type,
        "json": db_OrgUnit.json,
        "date": db_OrgUnit.date
    }


@ app.post("/OrgUnits")
async def add_OrgUnit(request: Request, db: Session = Depends(get_pgdb)):
    params = await request.json()
    db_OrgUnit = OrgUnit(name=params["name"],
                         type=params["type"],
                         json=params["json"])
    db.add(db_OrgUnit)
    db.commit()
    return OrgUnit_to_schema(db_OrgUnit)


@ app.get("/OrgUnits/{OrgUnit_id}")
async def get_OrgUnit(OrgUnit_id: int, db: Session = Depends(get_pgdb)):
    db_OrgUnit = db.get(OrgUnit, OrgUnit_id)
    if db_OrgUnit is None:
        raise HTTPException(status_code=404, detail="OrgUnit not found")
    return OrgUnit_to_schema(db_OrgUnit)


@ app.delete("/OrgUnits/{OrgUnit_id}")
async def delete_OrgUnit(OrgUnit_id: int, db: Session = Depends(get_pgdb)):
    db_OrgUnit = db.get(OrgUnit, OrgUnit_id)
    if db_OrgUnit is None:
        raise HTTPException(status_code=404, detail="OrgUnit not found")
    db_OrgUnit.date = date.today()
    db.commit()
    return OrgUnit_to_schema(db_OrgUnit)

IMG_NAME = "Demo"
IMG_FORMAT = "svg"


@app.get("/OrgTreeNodes")
async def vizualize(db: Session = Depends(get_pgdb)):
    dot = graphviz.Digraph(IMG_NAME, comment="Visualization")
    nodes = db.execute(text("SELECT * FROM \"OrgTreeNodes\"")).all()
    for elem in nodes:
        id = elem[0]
        date = elem[-1]
        node_style = "solid" if date == None else "dashed"
        info = str(id)
        if (elem[1] == "sensor"):
            db_Sensor = db.get(Sensor, elem[2])
            info += "\nSensor " + str(db_Sensor.id)
            db_SensorType = db.get(SensorType, db_Sensor.type_id)
            info += "\nfreq " + str(db_SensorType.freq) + \
                ", dim " + str(db_SensorType.dim)
        elif (elem[1] == "orgunit"):
            db_OrgUnit = db.get(OrgUnit, elem[2])
            info += "\nOrg unit " + str(db_OrgUnit.id)
            info += "\n" + db_OrgUnit.type
        dot.node(str(id), info, style=node_style)
    edges = db.execute(text(
        "SELECT * FROM \"OrgTreeEdges\" WHERE parent = false")).all()
    for elem in edges:
        date = elem[-1]
        edge_style = "solid" if date == None else "dashed"
        dot.edge(str(elem[1]), str(elem[2]), style=edge_style)
    dot.format = IMG_FORMAT
    dot.render(directory="./", view=False)
    return FileResponse("./" + IMG_NAME + ".gv." + IMG_FORMAT)

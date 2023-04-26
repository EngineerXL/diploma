def get_table_name(id: int):
    return "CH_Sensor_" + str(id)


def multi_create_table(id: int, db_SensorType: SensorType, db=Depends(get_chdb)):
    s, t = "", get_table_name(id)
    s += "CREATE TABLE IF NOT EXISTS " + t + " ( "
    s += "t DateTime64(6)"
    for i in range(db_SensorType.dim):
        s += ", value_" + str(i) + " Float64"
    s += ") ENGINE = MergeTree"
    s += " ORDER BY t"
    db.execute(s)

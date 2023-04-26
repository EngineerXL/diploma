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

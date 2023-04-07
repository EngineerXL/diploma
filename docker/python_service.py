from ch_data import *

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


@ app.post("/OrgTreeEdges")
async def post_OrgTreeEdge(request: Request, db: Session = Depends(get_pgdb)):
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


@ app.delete("/OrgTreeEdges")
async def delete_OrgTreeEdge(request: Request, db: Session = Depends(get_pgdb)):
    param_json = await request.json()
    try:
        res = delete_edge(param_json["id_u"], param_json["id_v"], db)
        return res
    except BaseException as ex:
        raise ex

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


@ app.post("/OrgTreeNodes")
async def post_OrgTreeNode(request: Request, db: Session = Depends(get_pgdb)):
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


@app.get("/OrgTreeNodes/{OrgTreeNode_id}")
async def get_OrgTreeNode(OrgTreeNode_id: int, db: Session = Depends(get_pgdb)):
    db_OrgTreeNode = db.get(OrgTreeNode, OrgTreeNode_id)
    if db_OrgTreeNode is None:
        raise HTTPException(status_code=404, detail="OrgTreeNode not found")
    return OrgTreeNode_to_schema(db_OrgTreeNode)


@ app.delete("/OrgTreeNodes/{OrgTreeNode_id}")
async def delete_OrgTreeNode(OrgTreeNode_id: int, db: Session = Depends(get_pgdb)):
    try:
        res = delete_node(OrgTreeNode_id, db)
        return res
    except BaseException as ex:
        raise ex


dbmode = "multi"


@app.put("/Mode")
async def chmode(mode: str):
    global dbmode
    dbmode = mode
    return dbmode


@ app.post("/OrgTreeNodes/{OrgTreeNode_id}/CH_Data")
async def post_OrgTreeNodeCHData(OrgTreeNode_id, time_begin, time_end, pg: Session = Depends(get_pgdb), ch=Depends(get_chdb)):
    interval = (datetime.strptime(
        time_begin, RFC3339_FORMAT), datetime.strptime(time_end, RFC3339_FORMAT))
    db_OrgTreeNode = pg.get(OrgTreeNode, OrgTreeNode_id)
    if db_OrgTreeNode is None:
        raise HTTPException(status_code=404,
                            detail="OrgTreeNode not found")
    dct_Sensors = dict()
    dfs(OrgTreeNode_id, dct_Sensors, pg)
    if (dbmode == "single"):
        single_post_ch_data(interval, dct_Sensors, ch)
    elif (dbmode == "multi"):
        multi_post_ch_data(interval, dct_Sensors, ch)

FNAME = "rep.csv"


@ app.get("/OrgTreeNodes/{OrgTreeNode_id}/CH_Data")
async def get_OrgTreeNodeData(OrgTreeNode_id, time_begin, time_end, pg: Session = Depends(get_pgdb), ch=Depends(get_chdb)):
    interval = (datetime.strptime(
        time_begin, RFC3339_FORMAT), datetime.strptime(time_end, RFC3339_FORMAT))
    db_OrgTreeNode = pg.get(OrgTreeNode, OrgTreeNode_id)
    if db_OrgTreeNode is None:
        raise HTTPException(status_code=404,
                            detail="OrgTreeNode not found")
    try:
        dct_Sensors = dict()
        dfs(OrgTreeNode_id, dct_Sensors, pg)
        if (dbmode == "single"):
            single_get_ch_data(FNAME, interval, dct_Sensors, ch)
        elif (dbmode == "multi"):
            multi_get_ch_data(FNAME, interval, dct_Sensors, ch)
        return FileResponse(FNAME)
    except BaseException as ex:
        raise ex


@ app.post("/SensorTypes")
async def add_SensorType(request: Request, db: Session = Depends(get_pgdb)):
    params = await request.json()
    db_SensorType = SensorType(freq=params["freq"],
                               dim=params["dim"],
                               info=params["info"])
    db.add(db_SensorType)
    db.commit()
    return SensorType_to_schema(db_SensorType)


@ app.post("/Sensors")
async def add_Sensor(request: Request, db: Session = Depends(get_pgdb), ch=Depends(get_chdb)):
    param_json = await request.json()
    SensorType_id = param_json["type_id"]
    db_SensorType = db.get(SensorType, SensorType_id)
    if (db_SensorType == None):
        raise HTTPException(status_code=500, detail="Sensor type not found")
    cnt_ch_tables = len(ch.execute("SHOW TABLES").fetchall()) + 1
    multi_create_table(cnt_ch_tables, db_SensorType, ch)
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


@ app.put("/Sensors/{Sensor_id}")
async def edit_Sensor(Sensor_id: int, request: Request, db: Session = Depends(get_pgdb), ch=Depends(get_chdb)):
    db_Sensor = db.get(Sensor, Sensor_id)
    if db_Sensor is None:
        raise HTTPException(status_code=404, detail="Sensor not found")
    param_json = await request.json()
    SensorType_id = param_json["type_id"]
    db_SensorType = db.get(SensorType, SensorType_id)
    if (db_SensorType == None):
        raise HTTPException(status_code=500,
                            detail="Sensor type not found")
    cnt_ch_tables = len(ch.execute("SHOW TABLES").fetchall()) + 1
    multi_create_table(cnt_ch_tables, db_SensorType, ch)
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

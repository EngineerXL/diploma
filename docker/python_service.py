from fastapi import Depends, FastAPI, HTTPException, Request
from sqlalchemy import create_engine, Column, MetaData, BigInteger, Text, Boolean, Date, exc
from sqlalchemy.sql import text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import Session
from datetime import date
import json
from fastapi.middleware.cors import CORSMiddleware

from clickhouse_sqlalchemy import Table, make_session, get_declarative_base, types, engines

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
    type = Column(BigInteger)
    date = Column(Date)


class SensorType(bases["pg"]):
    __tablename__ = "SensorTypes"
    id = Column(BigInteger, primary_key=True, index=True)
    freq = Column(BigInteger)
    dim = Column(BigInteger)
    info = Column(Text)


bases["pg"].metadata.create_all(bind=alchemy_engines["pg"])


class CH_Sensor(bases["ch"]):
    __tablename__ = "CH_Sensors"
    id = Column(types.Int64, primary_key=True, index=True)
    value = Column(types.Float64)
    date = Column(types.Date)

    __table_args__ = (
        engines.Memory(),
    )


try:
    # Emits CREATE TABLE statement
    r = CH_Sensor.__table__.create()
except BaseException as ex:
    # print(ex.args)
    pass


def get_chdb():
    db = make_session(alchemy_engines["ch"])
    try:
        yield db
    finally:
        db.close()


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


def CH_Sensor_to_schema(db_CH_Sensor: CH_Sensor):
    return {
        "id": db_CH_Sensor.id,
        "value": db_CH_Sensor.value,
        "date": db_CH_Sensor.date,
    }


@ app.post("/CH")
async def add_SensorType(request: Request, db: Session = Depends(get_chdb)):
    # params = await request.json()
    # db_CH_Sensor = SensorType(value=params["value"])
    db_CH_Sensor = CH_Sensor(value=1, date=date.today())
    db.add(db_CH_Sensor)
    db.commit()
    return SensorType_to_schema(db_CH_Sensor)


# @ app.get("/CH/{Sensor_id}")
# async def get_Sensor(Sensor_id: int, db: Session = Depends(get_pgdb)):
#     db_Sensor = db.get(Sensor, Sensor_id)
#     if db_Sensor is None:
#         raise HTTPException(status_code=404, detail="Sensor not found")
#     return Sensor_to_schema(db_Sensor)

def OrgTreeNode_to_schema(db_OrgTreeNode: OrgTreeNode):
    return {
        "id": db_OrgTreeNode.id,
        "type": db_OrgTreeNode.type,
        "object_id": db_OrgTreeNode.object_id,
        "date": db_OrgTreeNode.date
    }


@app.get("/OrgTreeNodes/{OrgTreeNode_id}")
async def get_OrgTreeNode(OrgTreeNode_id: int, db: Session = Depends(get_pgdb), db2: Session = Depends(get_chdb)):
    db_OrgTreeNode = db.get(OrgTreeNode, OrgTreeNode_id)
    if db_OrgTreeNode is None:
        raise HTTPException(status_code=404, detail="OrgTreeNode not found")
    return OrgTreeNode_to_schema(db_OrgTreeNode)


def db_get_adj(u: int, db: Session = Depends(get_pgdb)):
    parent = db.execute(text(
        "SELECT id_v FROM \"OrgTreeEdges\" WHERE id_u = " + str(u) + " AND parent = true")).fetchone()
    lst_adj = db.execute(text(
        "SELECT id_v FROM \"OrgTreeEdges\" WHERE id_u = " + str(u) + " AND parent = false")).all()
    return parent, lst_adj


def delete_node(OrgTreeNode_id: int, db: Session = Depends(get_pgdb)):
    db_OrgTreeNode = db.get(OrgTreeNode, OrgTreeNode_id)
    if db_OrgTreeNode is None:
        raise HTTPException(status_code=404, detail="OrgTreeNode not found")
    u = db_OrgTreeNode.id
    parent, adj = db_get_adj(u, db)
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
                status_code=404, detail="Sensor " + str(obj_id) + " not found")
    else:
        raise HTTPException(
            status_code=500, detail="Invalid type")
    db_OrgTreeNode = OrgTreeNode(type=node_type, object_id=obj_id)
    db.add(db_OrgTreeNode)
    db.commit()
    return OrgTreeNode_to_schema(db_OrgTreeNode)


def check_OrgTreeNode(OrgTreeNode_id: int, db: Session = Depends(get_pgdb)):
    db_OrgTreeNode = db.get(OrgTreeNode, OrgTreeNode_id)
    return False if db_OrgTreeNode == None else True


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
            status_code=404, detail="OrgTreeNode " + str(u) + " not found")
    if not (check_OrgTreeNode(v, db)):
        raise HTTPException(
            status_code=404, detail="OrgTreeNode " + str(v) + " not found")
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


def delete_edge(u: int, v: int, db: Depends(get_pgdb)):
    db_OrgTreeEdge = db_get_edge(u, v, db)
    if db_OrgTreeEdge is None:
        raise HTTPException(status_code=404, detail="OrgTreeEdge not found")
    db_OrgTreeEdge_uv = db.get(OrgTreeEdge, db_OrgTreeEdge.id)
    db_OrgTreeEdge_vu = db.get(OrgTreeEdge, inv_edge_id(db_OrgTreeEdge.id))
    db_OrgTreeEdge_uv.date = date.today()
    db_OrgTreeEdge_vu.date = date.today()
    if (db_OrgTreeEdge_uv.id_u != db_OrgTreeEdge_vu.id_v or db_OrgTreeEdge_uv.id_v != db_OrgTreeEdge_vu.id_u):
        raise HTTPException(status_code=500, detail="FAIL, incorrect edges!")
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
        "type": db_Sensor.type,
        "date": db_Sensor.date
    }


def check_SensorType(SensorType_id: int, db: Session = Depends(get_pgdb)):
    db_SensorType = db.get(SensorType, SensorType_id)
    return False if db_SensorType == None else True


@ app.post("/Sensors")
async def add_Sensor(request: Request, db: Session = Depends(get_pgdb)):
    param_json = await request.json()
    if not (check_SensorType(param_json["type"], db)):
        raise HTTPException(status_code=500, detail="Sensor type not found")
    db_Sensor = Sensor(type=param_json["type"])
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
async def edit_Sensor(Sensor_id: int, request: Request, db: Session = Depends(get_pgdb)):
    db_Sensor = db.get(Sensor, Sensor_id)
    if db_Sensor is None:
        raise HTTPException(status_code=404, detail="Sensor not found")
    param_json = await request.json()
    if not (check_SensorType(param_json["type"], db)):
        raise HTTPException(status_code=500, detail="Sensor type not found")
    db_Sensor.type = param_json["type"]
    db.commit()
    return Sensor_to_schema(db_Sensor)


@ app.delete("/Sensors/{Sensor_id}")
async def delete_Sensor(Sensor_id: int, request: Request, db: Session = Depends(get_pgdb)):
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

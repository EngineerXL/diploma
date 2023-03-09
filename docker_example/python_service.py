from fastapi import Depends, FastAPI, HTTPException, Request
from sqlalchemy import Column, BigInteger, Text, Boolean, exc
from sqlalchemy.sql import text
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import Session
import json
from fastapi.middleware.cors import CORSMiddleware

# Start SQL Alchemy
engine = create_engine(
    'postgresql+psycopg2://pguser:pguser@localhost/pgdb', echo=True)
conn = engine.connect()

Base = declarative_base()


class OrgTreeEdge(Base):
    __tablename__ = "OrgTreeEdges"
    id = Column(BigInteger, primary_key=True, index=True)
    id_u = Column(BigInteger)
    id_v = Column(BigInteger)
    parent = Column(Boolean)


class OrgTreeNode(Base):
    __tablename__ = "OrgTreeNodes"
    id = Column(BigInteger, primary_key=True, index=True)
    type = Column(Text)
    object_id = Column(BigInteger)


class OrgUnit(Base):
    __tablename__ = "OrgUnits"
    id = Column(BigInteger, primary_key=True, index=True)
    name = Column(Text)
    type = Column(Text)
    json = Column(Text)


class Sensor(Base):
    __tablename__ = "Sensors"
    id = Column(BigInteger, primary_key=True, index=True)
    type = Column(BigInteger)


class SensorType(Base):
    __tablename__ = "SensorTypes"
    id = Column(BigInteger, primary_key=True, index=True)
    freq = Column(BigInteger)
    dim = Column(BigInteger)
    info = Column(Text)


Base.metadata.create_all(engine)


def get_db():
    Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
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


def Sensor_to_schema(db_Sensor: Sensor):
    return {
        "id": db_Sensor.id,
        "type": db_Sensor.type
    }


def check_SensorType(SensorType_id: int, db: Session = Depends(get_db)):
    db_SensorType = db.execute(
        text("select * from \"SensorTypes\" where id = %s" % SensorType_id)).fetchone()
    return False if db_SensorType == None else True


@app.post("/Sensors")
async def add_Sensor(request: Request, db: Session = Depends(get_db)):
    param_json = await request.json()
    if not (check_SensorType(param_json["type"], db)):
        raise HTTPException(status_code=500, detail="Sensor type not found")
    db_Sensor = Sensor(type=param_json["type"])
    db.add(db_Sensor)
    db.commit()
    db.refresh(db_Sensor)
    db.commit()
    return Sensor_to_schema(db_Sensor)


@app.get("/Sensors/{Sensor_id}")
async def get_Sensor(Sensor_id: int, db: Session = Depends(get_db)):
    db_Sensor = db.get(Sensor, Sensor_id)
    if db_Sensor is None:
        raise HTTPException(status_code=404, detail="Sensor not found")
    return Sensor_to_schema(db_Sensor)


@app.put("/Sensors/{Sensor_id}")
async def edit_Sensor(Sensor_id: int, request: Request, db: Session = Depends(get_db)):
    db_Sensor = db.get(Sensor, Sensor_id)
    if db_Sensor is None:
        raise HTTPException(status_code=404, detail="Sensor not found")
    param_json = await request.json()
    if not (check_SensorType(param_json["type"], db)):
        raise HTTPException(status_code=500, detail="Sensor type not found")
    db_Sensor.type = param_json["type"]
    db.commit()
    return Sensor_to_schema(db_Sensor)


def SensorType_to_schema(db_SensorType: SensorType):
    return {
        "id": db_SensorType.id,
        "freq": db_SensorType.freq,
        "dim": db_SensorType.dim,
        "info": db_SensorType.info
    }


@app.post("/SensorTypes")
async def add_SensorType(request: Request, db: Session = Depends(get_db)):
    params = await request.json()
    db_SensorType = SensorType(freq=params["freq"],
                               dim=params["dim"],
                               info=params["info"])
    db.add(db_SensorType)
    db.commit()
    db.refresh(db_SensorType)
    db.commit()
    return SensorType_to_schema(db_SensorType)


def OrgUnit_to_schema(db_OrgUnit: OrgUnit):
    return {
        "id": db_OrgUnit.id,
        "name": db_OrgUnit.name,
        "type": db_OrgUnit.type,
        "json": db_OrgUnit.json
    }


@app.post("/OrgUnits")
async def add_OrgUnit(request: Request, db: Session = Depends(get_db)):
    params = await request.json()
    db_OrgUnit = OrgUnit(name=params["name"],
                         type=params["type"],
                         json=params["json"])
    db.add(db_OrgUnit)
    db.commit()
    db.refresh(db_OrgUnit)
    db.commit()
    return OrgUnit_to_schema(db_OrgUnit)


@app.get("/OrgUnits/{OrgUnit_id}")
async def get_OrgUnit(OrgUnit_id: int, db: Session = Depends(get_db)):
    db_OrgUnit = db.get(OrgUnit, OrgUnit_id)
    if db_OrgUnit is None:
        raise HTTPException(status_code=404, detail="OrgUnit not found")
    return OrgUnit_to_schema(db_OrgUnit)

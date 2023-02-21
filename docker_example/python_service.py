from fastapi import Depends, FastAPI, HTTPException, Request
from sqlalchemy import Column, Integer, String, ForeignKey, Date
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import Session
import json

# Start SQL Alchemy
engine = create_engine('postgresql+psycopg2://pguser:pguser@localhost/pgdb', echo = True)
conn = engine.connect() 

Base = declarative_base()

class Sensor(Base):
   __tablename__ = 'Sensor'
   id = Column(Integer,primary_key=True, index=True)
   type = Column(String)


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

def get_sensor_params(db_sensor: Sensor):
    return {
        "id": db_sensor.id,
        "type": db_sensor.type
    }

@app.get("/sensor/{sensor_id}")
async def readsensor(sensor_id: int, db: Session = Depends(get_db)):
    db_sensor = db.execute("select * from \"Sensor\" where id = %s" % sensor_id).first()
    if db_sensor is None:
        raise HTTPException(status_code=404, detail="Sensor not found")
    return get_sensor_params(db_sensor)

@app.post("/sensor")
async def add_sensor(request: Request, db: Session = Depends(get_db)):
    param_json = await request.json()
    
    db_sensor = Sensor(type = param_json['type'])
    db.add(db_sensor)
    db.commit()
    db.refresh(db_sensor)
    db.commit()
    return get_sensor_params(db_sensor)
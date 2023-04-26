class Sensor(bases["pg"]):
    __tablename__ = "Sensors"
    id = Column(BigInteger, primary_key=True, index=True)
    type_id = Column(BigInteger)
    ch_id = Column(BigInteger)
    date = Column(Date)


def Sensor_to_schema(db_Sensor: Sensor):
    return {
        "id": db_Sensor.id,
        "type_id": db_Sensor.type_id,
        "ch_id": db_Sensor.ch_id,
        "date": db_Sensor.date
    }


def check_Sensor(Sensor_id: int, db: Session = Depends(get_pgdb)):
    db_Sensor = db.get(Sensor, Sensor_id)
    return False if db_Sensor == None else True

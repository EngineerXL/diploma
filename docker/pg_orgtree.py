from fastapi import Depends, FastAPI, HTTPException, Request
from sqlalchemy import create_engine, Column, MetaData, BigInteger, Text, Boolean, Date
from sqlalchemy.sql import text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import Session
from fastapi.responses import FileResponse
from datetime import date, datetime, timedelta
from io import StringIO
from fastapi.middleware.cors import CORSMiddleware

from clickhouse_sqlalchemy import Table, make_session, get_declarative_base, types, engines

import csv
import graphviz
import numpy as np
import pandas as pd

# Start SQL Alchemy
alchemy_engines = {
    "pg": create_engine(
        "postgresql+psycopg2://pguser:pguser@localhost:25500/pgdb", echo=True),
    # "jdbc:ch://HOST.clickhouse.cloud:8443/?user=default&password=PASSWORD&ssl=true&custom_http_params=async_insert=1,wait_for_async_insert=0"
    "ch": create_engine("clickhouse+native://chuser:chuser@localhost:25501/chdb", echo=True)
}


metadatas = {
    "ch": MetaData(bind=alchemy_engines["ch"])
}

bases = {
    "pg": declarative_base(),
    "ch": get_declarative_base(metadata=MetaData(bind=alchemy_engines["ch"]))
}


def get_pgdb():
    Session = sessionmaker(
        autocommit=False, autoflush=False, bind=alchemy_engines["pg"])
    db = Session()
    try:
        yield db
    finally:
        db.close()


class OrgTreeEdge(bases["pg"]):
    __tablename__ = "OrgTreeEdges"
    id = Column(BigInteger, primary_key=True, index=True)
    id_u = Column(BigInteger)
    id_v = Column(BigInteger)
    parent = Column(Boolean)
    date = Column(Date)


def OrgTreeEdge_to_schema(db_OrgTreeEdge: OrgTreeEdge):
    return {
        "id": db_OrgTreeEdge.id,
        "id_u": db_OrgTreeEdge.id_u,
        "id_v": db_OrgTreeEdge.id_v,
        "parent": db_OrgTreeEdge.parent,
        "date": db_OrgTreeEdge.date
    }


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


class OrgTreeNode(bases["pg"]):
    __tablename__ = "OrgTreeNodes"
    id = Column(BigInteger, primary_key=True, index=True)
    type = Column(Text)
    object_id = Column(BigInteger)
    date = Column(Date)


def OrgTreeNode_to_schema(db_OrgTreeNode: OrgTreeNode):
    return {
        "id": db_OrgTreeNode.id,
        "type": db_OrgTreeNode.type,
        "object_id": db_OrgTreeNode.object_id,
        "date": db_OrgTreeNode.date
    }


def check_OrgTreeNode(OrgTreeNode_id: int, db: Session = Depends(get_pgdb)):
    db_OrgTreeNode = db.get(OrgTreeNode, OrgTreeNode_id)
    return False if db_OrgTreeNode == None or db_OrgTreeNode.date != None else True


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


class OrgUnit(bases["pg"]):
    __tablename__ = "OrgUnits"
    id = Column(BigInteger, primary_key=True, index=True)
    name = Column(Text)
    type = Column(Text)
    json = Column(Text)
    date = Column(Date)


def OrgUnit_to_schema(db_OrgUnit: OrgUnit):
    return {
        "id": db_OrgUnit.id,
        "name": db_OrgUnit.name,
        "type": db_OrgUnit.type,
        "json": db_OrgUnit.json,
        "date": db_OrgUnit.date
    }


def check_OrgUnit(OrgUnit_id: int, db: Session = Depends(get_pgdb)):
    db_OrgUnit = db.get(OrgUnit, OrgUnit_id)
    return False if db_OrgUnit == None else True


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


class SensorType(bases["pg"]):
    __tablename__ = "SensorTypes"
    id = Column(BigInteger, primary_key=True, index=True)
    freq = Column(BigInteger)
    dim = Column(BigInteger)
    info = Column(Text)


def SensorType_to_schema(db_SensorType: SensorType):
    return {
        "id": db_SensorType.id,
        "freq": db_SensorType.freq,
        "dim": db_SensorType.dim,
        "info": db_SensorType.info
    }


bases["pg"].metadata.create_all(bind=alchemy_engines["pg"])

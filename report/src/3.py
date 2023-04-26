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

def db_get_adj(u: int, db: Session = Depends(get_pgdb)):
    parent = db.execute(text(
        "SELECT id_v FROM \"OrgTreeEdges\" WHERE id_u = " + str(u) + " AND parent = true AND date is null")).fetchone()
    lst_adj = db.execute(text(
        "SELECT id_v FROM \"OrgTreeEdges\" WHERE id_u = " + str(u) + " AND parent = false AND date is null")).all()
    return parent, lst_adj

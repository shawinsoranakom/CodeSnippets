async def get_apps(
    category: Optional[str] = None,
    type: Optional[str] = None,
    featured: Optional[bool] = None,
    sponsored: Optional[bool] = None,
    limit: int = Query(default=20, le=10000),
    offset: int = Query(default=0)
):
    """Get apps with optional filters"""
    where_clauses = []
    if category:
        where_clauses.append(f"category = '{category}'")
    if type:
        where_clauses.append(f"type = '{type}'")
    if featured is not None:
        where_clauses.append(f"featured = {1 if featured else 0}")
    if sponsored is not None:
        where_clauses.append(f"sponsored = {1 if sponsored else 0}")

    where = " AND ".join(where_clauses) if where_clauses else None
    apps = db.get_all('apps', limit=limit, offset=offset, where=where)

    # Parse JSON fields
    for app in apps:
        if app.get('screenshots'):
            app['screenshots'] = json.loads(app['screenshots'])

    return json_response(apps)
async def search(q: str = Query(min_length=2)):
    """Search across apps and articles"""
    if len(q) < 2:
        return json_response({})

    results = db.search(q, tables=['apps', 'articles'])

    # Parse JSON fields in results
    for table, items in results.items():
        for item in items:
            if table == 'apps' and item.get('screenshots'):
                item['screenshots'] = json.loads(item['screenshots'])
            elif table == 'articles':
                if item.get('related_apps'):
                    item['related_apps'] = json.loads(item['related_apps'])
                if item.get('tags'):
                    item['tags'] = json.loads(item['tags'])

    return json_response(results, cache_time=1800)
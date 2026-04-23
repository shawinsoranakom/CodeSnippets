async def get_sponsors(active: Optional[bool] = True):
    """Get sponsors, default active only"""
    where = f"active = {1 if active else 0}" if active is not None else None
    sponsors = db.get_all('sponsors', where=where, limit=20)

    # Filter by date if active
    if active:
        now = datetime.now().isoformat()
        sponsors = [s for s in sponsors
                   if (not s.get('start_date') or s['start_date'] <= now) and
                      (not s.get('end_date') or s['end_date'] >= now)]

    return json_response(sponsors)
def get_source_names(source_ids):
    if not source_ids:
        return {}
    unique_ids = list(set([src_id for src_id in source_ids if src_id]))
    if not unique_ids:
        return {}
    try:
        sources_db_path = get_sources_db_path()
        check_query = """
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name='sources'
        """
        table_exists = execute_query(sources_db_path, check_query, fetch=True)
        if not table_exists:
            return {}
        placeholders = ",".join(["?"] * len(unique_ids))
        query = f"""
        SELECT id, name FROM sources
        WHERE id IN ({placeholders})
        """
        results = execute_query(sources_db_path, query, unique_ids, fetch=True)
        return {str(row["id"]): row["name"] for row in results} if results else {}
    except Exception as _:
        return {}
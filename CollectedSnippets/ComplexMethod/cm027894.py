def _execute_search(
    cursor,
    terms,
    from_date,
    operator,
    limit,
    use_categories=True,
    partial_match=False,
    days_fallback=0,
):
    if days_fallback > 0:
        try:
            from_date_obj = datetime.fromisoformat(from_date.replace("Z", "").split("+")[0])
            adjusted_date = (from_date_obj - timedelta(days=days_fallback)).isoformat()
            from_date = adjusted_date
        except Exception as e:
            print(f"Warning: Could not adjust date with fallback: {e}")
    base_query = """
        SELECT DISTINCT ca.id, ca.title, ca.url, ca.published_date, ca.summary as content, 
               ca.source_id, ca.feed_id
        FROM crawled_articles ca
        WHERE ca.processed = 1 AND ca.published_date >= ?
    """
    if use_categories:
        base_query = """
            SELECT DISTINCT ca.id, ca.title, ca.url, ca.published_date, ca.summary as content,
                   ca.source_id, ca.feed_id
            FROM crawled_articles ca
            LEFT JOIN article_categories ac ON ca.id = ac.article_id
            WHERE ca.processed = 1 AND ca.published_date >= ?
        """
    clauses, params = [], [from_date]
    for term in terms:
        term_clauses = []
        like = f"%{term}%"
        term_clauses.append("(ca.title LIKE ? OR ca.content LIKE ? OR ca.summary LIKE ?)")
        params.extend([like, like, like])
        if use_categories:
            term_clauses.append("(ac.category_name LIKE ?)")
            params.append(like)
        if term_clauses:
            clauses.append(f"({' OR '.join(term_clauses)})")
    where = f" {operator} ".join(clauses)
    sql = f"{base_query} AND ({where}) ORDER BY ca.published_date DESC LIMIT {limit}"
    cursor.execute(sql, params)
    return [dict(row) for row in cursor.fetchall()]
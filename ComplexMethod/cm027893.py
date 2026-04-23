def search_articles(
    prompt: str,
    db_path: str,
    api_key: str,
    operator: str = "OR",
    limit: int = 20,
    from_date: str = None,
    use_categories: bool = True,
    fallback_to_broader: bool = True,
) -> List[Dict[str, Any]]:
    if from_date is None:
        from_date = (datetime.now() - timedelta(hours=48)).isoformat()
    terms = extract_search_terms(prompt, api_key)
    if not terms:
        return []
    print(f"Search terms: {terms}")
    conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    results = []
    try:
        results = _execute_search(cursor, terms, from_date, operator, limit, use_categories)
        if fallback_to_broader and len(results) < min(5, limit):
            print(f"Initial search returned only {len(results)} results. Trying broader search...")
            if operator == "AND":
                broader_results = _execute_search(
                    cursor,
                    terms,
                    from_date,
                    "OR",
                    limit,
                    use_categories=True,
                )
                if len(broader_results) > len(results):
                    print(f"Broader search found {len(broader_results)} results")
                    results = broader_results
        if results:
            _add_source_names(cursor, results)
        for article in results:
            article["categories"] = _get_article_categories(cursor, article["id"])
    except Exception as e:
        print(f"Error searching articles: {e}")
    finally:
        conn.close()
    return results
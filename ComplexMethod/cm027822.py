def update_article_status(tracking_db_path, article_id, results=None, success=False, error_message=None):
    with db_connection(tracking_db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
        UPDATE crawled_articles
        SET ai_attempts = ai_attempts + 1
        WHERE id = ?
        """,
            (article_id,),
        )
        if success and results:
            categories = []
            if "categories" in results:
                if isinstance(results["categories"], str):
                    try:
                        categories = json.loads(results["categories"])
                    except json.JSONDecodeError:
                        categories = [c.strip() for c in results["categories"].split(",") if c.strip()]
                elif isinstance(results["categories"], list):
                    categories = results["categories"]
            cursor.execute(
                """
            UPDATE crawled_articles
            SET summary = ?, content = ?, processed = 1, ai_status = 'success'
            WHERE id = ?
            """,
                (results.get("summary", ""), results.get("content", ""), article_id),
            )
            conn.commit()
            if categories:
                save_article_categories(tracking_db_path, article_id, categories)
        else:
            cursor.execute(
                """
            UPDATE crawled_articles
            SET ai_status = 'error', ai_error = ?
            WHERE id = ?
            """,
                (error_message, article_id),
            )
            cursor.execute(
                """
            UPDATE crawled_articles
            SET ai_status = 'failed'
            WHERE id = ? AND ai_attempts >= 3
            """,
                (article_id,),
            )
            conn.commit()
        return cursor.rowcount
async def get_article(self, article_id: int) -> Article:
        """Get a specific article by ID."""
        try:
            article_query = """
            SELECT id, title, url, published_date, content, summary, feed_id,
                   metadata, ai_status
            FROM crawled_articles
            WHERE id = ? AND processed = 1
            """
            article = await tracking_db.execute_query(article_query, (article_id,), fetch=True, fetch_one=True)
            if not article:
                raise HTTPException(status_code=404, detail="Article not found")
            if article.get("feed_id"):
                source_query = """
                SELECT s.name as source_name
                FROM source_feeds sf
                JOIN sources s ON sf.source_id = s.id
                WHERE sf.id = ?
                """
                source_result = await sources_db.execute_query(source_query, (article["feed_id"],), fetch=True, fetch_one=True)
                if source_result:
                    article["source_name"] = source_result["source_name"]
                else:
                    article["source_name"] = "Unknown Source"
            else:
                article["source_name"] = "Unknown Source"
            article.pop("feed_id", None)
            if article.get("metadata"):
                try:
                    article["metadata"] = json.loads(article["metadata"])
                except json.JSONDecodeError:
                    article["metadata"] = {}
            article["categories"] = await self.get_article_categories(article_id)
            return article
        except Exception as e:
            if isinstance(e, HTTPException):
                raise e
            raise HTTPException(status_code=500, detail=f"Error fetching article: {str(e)}")
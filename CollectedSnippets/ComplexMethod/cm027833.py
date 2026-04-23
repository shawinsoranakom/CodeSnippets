async def get_trending_topics(
        self, 
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get trending topics with sentiment breakdown."""
        try:
            query_parts = [
                """
                WITH topic_data AS (
                    SELECT 
                        json_each.value as topic,
                        sentiment,
                        COUNT(*) as count
                    FROM 
                        posts,
                        json_each(posts.tags)
                    WHERE tags IS NOT NULL
                """
            ]
            params = []
            if date_from:
                query_parts.append("AND datetime(post_timestamp) >= datetime(?)")
                params.append(date_from)
            if date_to:
                query_parts.append("AND datetime(post_timestamp) <= datetime(?)")
                params.append(date_to)  
            query_parts.append(
                """
                GROUP BY 
                    json_each.value, sentiment
                )
                SELECT 
                    topic,
                    SUM(count) as total_count,
                    SUM(CASE WHEN sentiment = 'positive' THEN count ELSE 0 END) as positive_count,
                    SUM(CASE WHEN sentiment = 'negative' THEN count ELSE 0 END) as negative_count,
                    SUM(CASE WHEN sentiment = 'neutral' THEN count ELSE 0 END) as neutral_count,
                    SUM(CASE WHEN sentiment = 'critical' THEN count ELSE 0 END) as critical_count
                FROM 
                    topic_data
                GROUP BY 
                    topic
                ORDER BY 
                    total_count DESC
                LIMIT ?
                """
            )
            params.append(limit)
            query = " ".join(query_parts)
            result = await social_media_db.execute_query(query, tuple(params), fetch=True)
            for topic in result:
                total = topic["total_count"]
                topic["positive_percent"] = (topic["positive_count"] / total) * 100 if total > 0 else 0
                topic["negative_percent"] = (topic["negative_count"] / total) * 100 if total > 0 else 0
                topic["neutral_percent"] = (topic["neutral_count"] / total) * 100 if total > 0 else 0
                topic["critical_percent"] = (topic["critical_count"] / total) * 100 if total > 0 else 0
            return result
        except Exception as e:
            if isinstance(e, HTTPException):
                raise e
            raise HTTPException(status_code=500, detail=f"Error fetching trending topics: {str(e)}")
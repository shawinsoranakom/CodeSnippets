async def get_user_sentiment(
        self,
        limit: int = 10,
        platform: Optional[str] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Get users with their sentiment breakdown."""
        try:
            query_parts = [
                """
                SELECT 
                    user_handle, 
                    user_display_name,
                    COUNT(*) as total_posts,
                    SUM(CASE WHEN sentiment = 'positive' THEN 1 ELSE 0 END) as positive_count,
                    SUM(CASE WHEN sentiment = 'negative' THEN 1 ELSE 0 END) as negative_count,
                    SUM(CASE WHEN sentiment = 'neutral' THEN 1 ELSE 0 END) as neutral_count,
                    SUM(CASE WHEN sentiment = 'critical' THEN 1 ELSE 0 END) as critical_count
                FROM posts
                WHERE user_handle IS NOT NULL
                """
            ]
            params = []
            if platform:
                query_parts.append("AND platform = ?")
                params.append(platform)
            if date_from:
                query_parts.append("AND datetime(post_timestamp) >= datetime(?)")
                params.append(date_from)
            if date_to:
                query_parts.append("AND datetime(post_timestamp) <= datetime(?)")
                params.append(date_to)
            query_parts.extend(["GROUP BY user_handle, user_display_name", "ORDER BY total_posts DESC", "LIMIT ?"])
            params.append(limit)
            query = " ".join(query_parts)
            result = await social_media_db.execute_query(query, tuple(params), fetch=True)
            for user in result:
                total = user["total_posts"]
                user["positive_percent"] = (user["positive_count"] / total) * 100 if total > 0 else 0
                user["negative_percent"] = (user["negative_count"] / total) * 100 if total > 0 else 0
                user["neutral_percent"] = (user["neutral_count"] / total) * 100 if total > 0 else 0
                user["critical_percent"] = (user["critical_count"] / total) * 100 if total > 0 else 0
            return result
        except Exception as e:
            if isinstance(e, HTTPException):
                raise e
            raise HTTPException(status_code=500, detail=f"Error fetching user sentiment: {str(e)}")
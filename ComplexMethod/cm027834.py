async def get_sentiment_over_time(
        self, 
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        platform: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get sentiment trends over time."""
        try:
            date_range_query = ""
            if date_from and date_to:
                date_range_query = f"""
                WITH RECURSIVE date_range(date) AS (
                    SELECT date('{date_from}')
                    UNION ALL
                    SELECT date(date, '+1 day')
                    FROM date_range
                    WHERE date < date('{date_to}')
                )
                SELECT date as post_date FROM date_range
                """
            else:
                days_ago = (datetime.now() - timedelta(days=30)).isoformat()
                date_range_query = f"""
                WITH RECURSIVE date_range(date) AS (
                    SELECT date('{days_ago}')
                    UNION ALL
                    SELECT date(date, '+1 day')
                    FROM date_range
                    WHERE date < date('now')
                )
                SELECT date as post_date FROM date_range
                """
            query_parts = [
                f"""
                WITH dates AS (
                    {date_range_query}
                )
                SELECT 
                    dates.post_date,
                    COALESCE(SUM(CASE WHEN sentiment = 'positive' THEN 1 ELSE 0 END), 0) as positive_count,
                    COALESCE(SUM(CASE WHEN sentiment = 'negative' THEN 1 ELSE 0 END), 0) as negative_count,
                    COALESCE(SUM(CASE WHEN sentiment = 'neutral' THEN 1 ELSE 0 END), 0) as neutral_count,
                    COALESCE(SUM(CASE WHEN sentiment = 'critical' THEN 1 ELSE 0 END), 0) as critical_count,
                    COUNT(posts.post_id) as total_count
                FROM 
                    dates
                LEFT JOIN 
                    posts ON date(posts.post_timestamp) = dates.post_date
                """
            ]
            params = []
            if platform:
                query_parts.append("AND posts.platform = ?")
                params.append(platform)
            query_parts.append("GROUP BY dates.post_date ORDER BY dates.post_date")
            query = " ".join(query_parts)
            result = await social_media_db.execute_query(query, tuple(params), fetch=True)
            for day in result:
                total = day["total_count"]
                day["positive_percent"] = (day["positive_count"] / total) * 100 if total > 0 else 0
                day["negative_percent"] = (day["negative_count"] / total) * 100 if total > 0 else 0
                day["neutral_percent"] = (day["neutral_count"] / total) * 100 if total > 0 else 0
                day["critical_percent"] = (day["critical_count"] / total) * 100 if total > 0 else 0
            return result
        except Exception as e:
            if isinstance(e, HTTPException):
                raise e
            raise HTTPException(status_code=500, detail=f"Error fetching sentiment over time: {str(e)}")
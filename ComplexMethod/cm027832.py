async def get_category_sentiment(self, date_from: Optional[str] = None, date_to: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get sentiment distribution by category."""
        try:
            date_filter = ""
            params = []
            if date_from or date_to:
                date_filter = "WHERE "
                if date_from:
                    date_filter += "datetime(p.post_timestamp) >= datetime(?)"
                    params.append(date_from)
                    if date_to:
                        date_filter += " AND "
                if date_to:
                    date_filter += "datetime(p.post_timestamp) <= datetime(?)"
                    params.append(date_to)
            query = f"""
            WITH category_data AS (
                SELECT 
                    json_each.value as category,
                    sentiment,
                    COUNT(*) as count
                FROM 
                    posts p,
                    json_each(p.categories)
                {date_filter}
                GROUP BY 
                    json_each.value, sentiment
            )
            SELECT 
                category,
                SUM(count) as total_count,
                SUM(CASE WHEN sentiment = 'positive' THEN count ELSE 0 END) as positive_count,
                SUM(CASE WHEN sentiment = 'negative' THEN count ELSE 0 END) as negative_count,
                SUM(CASE WHEN sentiment = 'neutral' THEN count ELSE 0 END) as neutral_count,
                SUM(CASE WHEN sentiment = 'critical' THEN count ELSE 0 END) as critical_count
            FROM 
                category_data
            GROUP BY 
                category
            ORDER BY 
                total_count DESC
            """
            result = await social_media_db.execute_query(query, tuple(params), fetch=True)
            for category in result:
                total = category["total_count"]
                category["positive_percent"] = (category["positive_count"] / total) * 100 if total > 0 else 0
                category["negative_percent"] = (category["negative_count"] / total) * 100 if total > 0 else 0
                category["neutral_percent"] = (category["neutral_count"] / total) * 100 if total > 0 else 0
                category["critical_percent"] = (category["critical_count"] / total) * 100 if total > 0 else 0
            return result
        except Exception as e:
            if isinstance(e, HTTPException):
                raise e
            raise HTTPException(status_code=500, detail=f"Error fetching category sentiment: {str(e)}")
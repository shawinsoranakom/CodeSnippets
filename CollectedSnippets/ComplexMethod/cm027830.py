async def get_categories(self, date_from: Optional[str] = None, date_to: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get all categories with post counts."""
        try:
            query_parts = ["SELECT categories FROM posts WHERE categories IS NOT NULL"]
            params = []
            if date_from:
                query_parts.append("AND datetime(post_timestamp) >= datetime(?)")
                params.append(date_from)
            if date_to:
                query_parts.append("AND datetime(post_timestamp) <= datetime(?)")
                params.append(date_to) 
            query = " ".join(query_parts)
            result = await social_media_db.execute_query(query, tuple(params), fetch=True)
            category_counts = {}
            for row in result:
                if row.get("categories"):
                    try:
                        categories = json.loads(row["categories"])
                        for category in categories:
                            if category in category_counts:
                                category_counts[category] += 1
                            else:
                                category_counts[category] = 1
                    except json.JSONDecodeError:
                        pass
            return [{"category": category, "post_count": count} for category, count in sorted(category_counts.items(), key=lambda x: x[1], reverse=True)]
        except Exception as e:
            if isinstance(e, HTTPException):
                raise e
            raise HTTPException(status_code=500, detail=f"Error fetching categories: {str(e)}")
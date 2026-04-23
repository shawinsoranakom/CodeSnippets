async def get_influential_posts(
        self, 
        sentiment: Optional[str] = None,
        limit: int = 5,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get most influential posts by engagement, optionally filtered by sentiment."""
        try:
            query_parts = [
                """
                SELECT *,
                    (COALESCE(engagement_reply_count, 0) + 
                    COALESCE(engagement_retweet_count, 0) + 
                    COALESCE(engagement_like_count, 0) + 
                    COALESCE(engagement_bookmark_count, 0)) as total_engagement
                FROM posts
                WHERE 1=1
                """
            ]
            params = []
            if sentiment:
                query_parts.append("AND sentiment = ?")
                params.append(sentiment)  
            if date_from:
                query_parts.append("AND datetime(post_timestamp) >= datetime(?)")
                params.append(date_from)
            if date_to:
                query_parts.append("AND datetime(post_timestamp) <= datetime(?)")
                params.append(date_to)
            query_parts.extend(["ORDER BY total_engagement DESC", "LIMIT ?"])
            params.append(limit)
            query = " ".join(query_parts)
            result = await social_media_db.execute_query(query, tuple(params), fetch=True)
            processed_posts = []
            for post in result:
                post_dict = dict(post)
                if post_dict.get("media"):
                    try:
                        post_dict["media"] = json.loads(post_dict["media"])
                    except json.JSONDecodeError:
                        post_dict["media"] = []
                if post_dict.get("categories"):
                    try:
                        post_dict["categories"] = json.loads(post_dict["categories"])
                    except json.JSONDecodeError:
                        post_dict["categories"] = []
                if post_dict.get("tags"):
                    try:
                        post_dict["tags"] = json.loads(post_dict["tags"])
                    except json.JSONDecodeError:
                        post_dict["tags"] = []
                post_dict["engagement"] = {
                    "replies": post_dict.pop("engagement_reply_count", 0),
                    "retweets": post_dict.pop("engagement_retweet_count", 0),
                    "likes": post_dict.pop("engagement_like_count", 0),
                    "bookmarks": post_dict.pop("engagement_bookmark_count", 0),
                    "views": post_dict.pop("engagement_view_count", 0),
                }
                processed_posts.append(post_dict)
            return processed_posts
        except Exception as e:
            if isinstance(e, HTTPException):
                raise e
            raise HTTPException(status_code=500, detail=f"Error fetching influential posts: {str(e)}")
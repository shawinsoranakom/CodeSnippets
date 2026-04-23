async def get_engagement_stats(
        self,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get overall engagement statistics."""
        try:
            query_parts = [
                """
                SELECT 
                    AVG(COALESCE(engagement_reply_count, 0)) as avg_replies,
                    AVG(COALESCE(engagement_retweet_count, 0)) as avg_retweets,
                    AVG(COALESCE(engagement_like_count, 0)) as avg_likes,
                    AVG(COALESCE(engagement_bookmark_count, 0)) as avg_bookmarks,
                    AVG(COALESCE(engagement_view_count, 0)) as avg_views,
                    MAX(COALESCE(engagement_reply_count, 0)) as max_replies,
                    MAX(COALESCE(engagement_retweet_count, 0)) as max_retweets,
                    MAX(COALESCE(engagement_like_count, 0)) as max_likes,
                    MAX(COALESCE(engagement_bookmark_count, 0)) as max_bookmarks,
                    MAX(COALESCE(engagement_view_count, 0)) as max_views,
                    COUNT(*) as total_posts,
                    COUNT(DISTINCT user_handle) as unique_authors
                FROM posts
                WHERE 1=1
                """
            ]
            params = []
            if date_from:
                query_parts.append("AND datetime(post_timestamp) >= datetime(?)")
                params.append(date_from)
            if date_to:
                query_parts.append("AND datetime(post_timestamp) <= datetime(?)")
                params.append(date_to)
            query = " ".join(query_parts)
            result = await social_media_db.execute_query(query, tuple(params), fetch=True, fetch_one=True)
            if not result:
                return {"avg_engagement": 0, "total_posts": 0, "unique_authors": 0}
            result_dict = dict(result)
            result_dict["avg_engagement"] = (
                result_dict["avg_replies"] + result_dict["avg_retweets"] + result_dict["avg_likes"] + result_dict["avg_bookmarks"]
            )
            platform_query_parts = [
                """
                SELECT 
                    platform, 
                    COUNT(*) as post_count
                FROM posts
                WHERE 1=1
                """
            ]
            if date_from:
                platform_query_parts.append("AND datetime(post_timestamp) >= datetime(?)")
            if date_to:
                platform_query_parts.append("AND datetime(post_timestamp) <= datetime(?)")
            platform_query_parts.extend([
                "GROUP BY platform",
                "ORDER BY post_count DESC",
                "LIMIT 10"
            ])
            platforms = await social_media_db.execute_query(
                " ".join(platform_query_parts), 
                tuple(params), 
                fetch=True
            )
            result_dict["platforms"] = platforms
            return result_dict
        except Exception as e:
            if isinstance(e, HTTPException):
                raise e
            raise HTTPException(status_code=500, detail=f"Error fetching engagement stats: {str(e)}")
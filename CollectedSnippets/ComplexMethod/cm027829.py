async def get_post(self, post_id: str) -> Dict[str, Any]:
        """Get a specific post by ID."""
        try:
            query = "SELECT * FROM posts WHERE post_id = ?"
            post = await social_media_db.execute_query(query, (post_id,), fetch=True, fetch_one=True)
            if not post:
                raise HTTPException(status_code=404, detail="Post not found")
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
            return post_dict
        except Exception as e:
            if isinstance(e, HTTPException):
                raise e
            raise HTTPException(status_code=500, detail=f"Error fetching social media post: {str(e)}")
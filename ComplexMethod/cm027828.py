async def get_posts(
        self,
        page: int = 1,
        per_page: int = 10,
        platform: Optional[str] = None,
        user_handle: Optional[str] = None,
        sentiment: Optional[str] = None,
        category: Optional[str] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        search: Optional[str] = None,
    ) -> PaginatedPosts:
        """Get social media posts with pagination and filtering."""
        try:
            offset = (page - 1) * per_page
            query_parts = [
                "SELECT * FROM posts",
                "WHERE 1=1",
            ]
            query_params = []
            if platform:
                query_parts.append("AND platform = ?")
                query_params.append(platform)
            if user_handle:
                query_parts.append("AND user_handle = ?")
                query_params.append(user_handle)
            if sentiment:
                query_parts.append("AND sentiment = ?")
                query_params.append(sentiment)
            if category:
                query_parts.append("AND categories LIKE ?")
                query_params.append(f'%"{category}"%')
            if date_from:
                query_parts.append("AND datetime(post_timestamp) >= datetime(?)")
                query_params.append(date_from)
            if date_to:
                query_parts.append("AND datetime(post_timestamp) <= datetime(?)")
                query_params.append(date_to)
            if search:
                query_parts.append("AND (post_text LIKE ? OR user_display_name LIKE ? OR user_handle LIKE ?)")
                search_param = f"%{search}%"
                query_params.extend([search_param, search_param, search_param])
            count_query = " ".join(query_parts).replace("SELECT *", "SELECT COUNT(*)")
            total_posts = await social_media_db.execute_query(count_query, tuple(query_params), fetch=True, fetch_one=True)
            total_count = total_posts.get("COUNT(*)", 0) if total_posts else 0
            query_parts.append("ORDER BY datetime(post_timestamp) DESC, post_id DESC")
            query_parts.append("LIMIT ? OFFSET ?")
            query_params.extend([per_page, offset])
            posts_query = " ".join(query_parts)
            posts_data = await social_media_db.execute_query(posts_query, tuple(query_params), fetch=True)
            posts = []
            for post in posts_data:
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
                posts.append(post_dict)
            total_pages = (total_count + per_page - 1) // per_page if total_count > 0 else 0
            has_next = page < total_pages
            has_prev = page > 1
            return PaginatedPosts(
                items=posts,
                total=total_count,
                page=page,
                per_page=per_page,
                total_pages=total_pages,
                has_next=has_next,
                has_prev=has_prev,
            )
        except Exception as e:
            if isinstance(e, HTTPException):
                raise e
            raise HTTPException(status_code=500, detail=f"Error fetching social media posts: {str(e)}")
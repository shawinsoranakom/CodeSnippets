async def update_feed(self, feed_id: int, feed_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing feed."""
        try:
            feed_query = "SELECT id, source_id FROM source_feeds WHERE id = ?"
            feed = await sources_db.execute_query(feed_query, (feed_id,), fetch=True, fetch_one=True)
            if not feed:
                raise HTTPException(status_code=404, detail="Feed not found")
            update_fields = []
            update_params = []
            if "feed_url" in feed_data:
                update_fields.append("feed_url = ?")
                update_params.append(feed_data["feed_url"])
            if "feed_type" in feed_data:
                update_fields.append("feed_type = ?")
                update_params.append(feed_data["feed_type"])
            if "is_active" in feed_data:
                update_fields.append("is_active = ?")
                update_params.append(feed_data["is_active"])
            if not update_fields:
                return await self.get_source_feeds(feed["source_id"])
            update_params.append(feed_id)
            update_query = f"""
            UPDATE source_feeds
            SET {", ".join(update_fields)}
            WHERE id = ?
            """
            await sources_db.execute_query(update_query, tuple(update_params))
            return await self.get_source_feeds(feed["source_id"])
        except Exception as e:
            if isinstance(e, HTTPException):
                raise e
            if "UNIQUE constraint failed" in str(e) and "feed_url" in str(e):
                raise HTTPException(status_code=409, detail="Feed URL already exists")
            raise HTTPException(status_code=500, detail=f"Error updating feed: {str(e)}")
async def create_source(self, source_data: SourceCreate) -> Dict[str, Any]:
        """Create a new source."""
        try:
            source_query = """
            INSERT INTO sources (name, url, description, is_active, created_at)
            VALUES (?, ?, ?, ?, ?)
            """
            source_params = (source_data.name, source_data.url, source_data.description, source_data.is_active, datetime.now().isoformat())
            source_id = await sources_db.execute_query(source_query, source_params)
            if source_data.categories:
                for category_name in source_data.categories:
                    await self.add_source_category(source_id, category_name)
            elif hasattr(source_data, "category") and source_data.category:
                await self.add_source_category(source_id, source_data.category)
            if source_data.feeds:
                for feed in source_data.feeds:
                    await self.add_feed_to_source(source_id, feed)
            return await self.get_source(source_id)
        except Exception as e:
            if isinstance(e, HTTPException):
                raise e
            if "UNIQUE constraint failed" in str(e) and "name" in str(e):
                raise HTTPException(status_code=409, detail="Source with this name already exists")
            raise HTTPException(status_code=500, detail=f"Error creating source: {str(e)}")
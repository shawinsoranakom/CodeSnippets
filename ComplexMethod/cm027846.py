async def update_source(self, source_id: int, source_data: SourceUpdate) -> Dict[str, Any]:
        """Update an existing source."""
        try:
            await self.get_source(source_id)
            update_fields = []
            update_params = []
            if source_data.name is not None:
                update_fields.append("name = ?")
                update_params.append(source_data.name)
            if source_data.url is not None:
                update_fields.append("url = ?")
                update_params.append(source_data.url)
            if source_data.description is not None:
                update_fields.append("description = ?")
                update_params.append(source_data.description)
            if source_data.is_active is not None:
                update_fields.append("is_active = ?")
                update_params.append(source_data.is_active)
            if update_fields:
                update_params.append(source_id)
                update_query = f"""
                UPDATE sources
                SET {", ".join(update_fields)}
                WHERE id = ?
                """
                await sources_db.execute_query(update_query, tuple(update_params))
            if source_data.categories is not None:
                delete_categories_query = "DELETE FROM source_categories WHERE source_id = ?"
                await sources_db.execute_query(delete_categories_query, (source_id,))
                if source_data.categories:
                    for category_name in source_data.categories:
                        await self.add_source_category(source_id, category_name)
            elif hasattr(source_data, "category") and source_data.category is not None:
                delete_categories_query = "DELETE FROM source_categories WHERE source_id = ?"
                await sources_db.execute_query(delete_categories_query, (source_id,))
                if source_data.category:
                    await self.add_source_category(source_id, source_data.category)
            return await self.get_source(source_id)
        except Exception as e:
            if isinstance(e, HTTPException):
                raise e
            if "UNIQUE constraint failed" in str(e) and "name" in str(e):
                raise HTTPException(status_code=409, detail="Source with this name already exists")
            raise HTTPException(status_code=500, detail=f"Error updating source: {str(e)}")
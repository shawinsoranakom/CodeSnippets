async def update_config(self, config_id: int, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing podcast configuration."""
        try:
            allowed_fields = [
                "name",
                "description",
                "prompt",
                "time_range_hours",
                "limit_articles",
                "is_active",
                "tts_engine",
                "language_code",
                "podcast_script_prompt",
                "image_prompt",
            ]
            set_clauses = []
            params = []
            set_clauses.append("updated_at = ?")
            params.append(datetime.now().isoformat())
            for field, value in updates.items():
                if field in allowed_fields:
                    if field == "is_active":
                        value = 1 if value else 0
                    set_clauses.append(f"{field} = ?")
                    params.append(value)
            if not set_clauses:
                return await self.get_config(config_id)
            params.append(config_id)
            update_query = f"""
            UPDATE podcast_configs
            SET {", ".join(set_clauses)}
            WHERE id = ?
            """
            await tasks_db.execute_query(update_query, tuple(params))
            return await self.get_config(config_id)
        except Exception as e:
            if isinstance(e, HTTPException):
                raise e
            raise HTTPException(status_code=500, detail=f"Error updating podcast configuration: {str(e)}")
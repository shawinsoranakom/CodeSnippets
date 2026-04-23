async def update_podcast(self, podcast_id: int, podcast_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update podcast metadata and content."""
        try:
            existing = await self.get_podcast(podcast_id)
            if not existing:
                raise HTTPException(status_code=404, detail="Podcast not found")
            fields = []
            params = []
            if "title" in podcast_data:
                fields.append("title = ?")
                params.append(podcast_data["title"])
            if "date" in podcast_data:
                fields.append("date = ?")
                params.append(podcast_data["date"])
            if "content" in podcast_data and isinstance(podcast_data["content"], dict):
                fields.append("content_json = ?")
                params.append(json.dumps(podcast_data["content"]))
            if "audio_generated" in podcast_data:
                fields.append("audio_generated = ?")
                params.append(1 if podcast_data["audio_generated"] else 0)
            if "audio_path" in podcast_data:
                fields.append("audio_path = ?")
                params.append(podcast_data["audio_path"])
            if "banner_img_path" in podcast_data:
                fields.append("banner_img_path = ?")
                params.append(podcast_data["banner_img_path"])
            if "sources" in podcast_data:
                fields.append("sources_json = ?")
                params.append(json.dumps(podcast_data["sources"]))
            if "language_code" in podcast_data:
                fields.append("language_code = ?")
                params.append(podcast_data["language_code"])
            if "tts_engine" in podcast_data:
                fields.append("tts_engine = ?")
                params.append(podcast_data["tts_engine"])
            if not fields:
                return existing
            params.append(podcast_id)
            query = f"""
            UPDATE podcasts SET {", ".join(fields)}
            WHERE id = ?
            """
            await podcasts_db.execute_query(query, tuple(params))
            return await self.get_podcast(podcast_id)
        except Exception as e:
            if isinstance(e, HTTPException):
                raise e
            raise HTTPException(status_code=500, detail=f"Error updating podcast: {str(e)}")
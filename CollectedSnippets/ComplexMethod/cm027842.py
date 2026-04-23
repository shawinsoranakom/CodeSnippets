async def delete_podcast(self, podcast_id: int, delete_assets: bool = False) -> bool:
        """Delete a podcast from the database."""
        try:
            existing = await self.get_podcast(podcast_id)
            if not existing:
                raise HTTPException(status_code=404, detail="Podcast not found")
            query = "DELETE FROM podcasts WHERE id = ?"
            result = await podcasts_db.execute_query(query, (podcast_id,))
            if delete_assets:
                if existing.get("audio_path"):
                    audio_path = os.path.join(AUDIO_DIR, existing["audio_path"])
                    if os.path.exists(audio_path):
                        os.remove(audio_path)
                if existing.get("banner_img_path"):
                    img_path = os.path.join(IMAGE_DIR, existing["banner_img_path"])
                    if os.path.exists(img_path):
                        os.remove(img_path)
            return result > 0
        except Exception as e:
            if isinstance(e, HTTPException):
                raise e
            raise HTTPException(status_code=500, detail=f"Error deleting podcast: {str(e)}")
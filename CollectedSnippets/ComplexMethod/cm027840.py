async def get_podcast(self, podcast_id: int) -> Optional[Dict[str, Any]]:
        """Get a specific podcast by ID without content."""
        try:
            query = """
            SELECT id, title, date, audio_generated, audio_path, banner_img_path,
                language_code, tts_engine, created_at, banner_images
            FROM podcasts
            WHERE id = ?
            """
            podcast = await podcasts_db.execute_query(query, (podcast_id,), fetch=True, fetch_one=True)
            if not podcast:
                raise HTTPException(status_code=404, detail="Podcast not found")
            podcast["audio_generated"] = bool(podcast.get("audio_generated", 0))
            if podcast.get("banner_img_path"):
                podcast["banner_img"] = podcast.get("banner_img_path")
            else:
                podcast["banner_img"] = None
            podcast.pop("banner_img_path", None)
            podcast["identifier"] = str(podcast.get("id", ""))
            sources_query = "SELECT sources_json FROM podcasts WHERE id = ?"
            sources_result = await podcasts_db.execute_query(sources_query, (podcast_id,), fetch=True, fetch_one=True)
            sources = []
            if sources_result and sources_result.get("sources_json"):
                try:
                    parsed_sources = json.loads(sources_result["sources_json"])
                    if isinstance(parsed_sources, list):
                        sources = parsed_sources
                    else:
                        sources = [parsed_sources]
                except json.JSONDecodeError:
                    sources = []
            podcast["sources"] = sources

            try:
                banner_images = json.loads(podcast.get("banner_images", "[]"))
            except json.JSONDecodeError:
                banner_images = []
            podcast["banner_images"] = banner_images

            return podcast
        except Exception as e:
            if isinstance(e, HTTPException):
                raise e
            raise HTTPException(status_code=500, detail=f"Error loading podcast: {str(e)}")
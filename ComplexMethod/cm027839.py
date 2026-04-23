async def get_podcasts(
        self,
        page: int = 1,
        per_page: int = 10,
        search: str = None,
        date_from: str = None,
        date_to: str = None,
        language_code: str = None,
        tts_engine: str = None,
        has_audio: bool = None,
    ) -> Dict[str, Any]:
        """
        Get a paginated list of podcasts with optional filtering.
        """
        try:
            offset = (page - 1) * per_page
            count_query = "SELECT COUNT(*) as count FROM podcasts"
            query = """
            SELECT id, title, date, audio_generated, audio_path, banner_img_path,
                   language_code, tts_engine, created_at
            FROM podcasts
            """
            where_conditions = []
            params = []
            if search:
                where_conditions.append("(title LIKE ?)")
                search_param = f"%{search}%"
                params.append(search_param)
            if date_from:
                where_conditions.append("date >= ?")
                params.append(date_from)
            if date_to:
                where_conditions.append("date <= ?")
                params.append(date_to)
            if language_code:
                where_conditions.append("language_code = ?")
                params.append(language_code)
            if tts_engine:
                where_conditions.append("tts_engine = ?")
                params.append(tts_engine)
            if has_audio is not None:
                where_conditions.append("audio_generated = ?")
                params.append(1 if has_audio else 0)
            if where_conditions:
                where_clause = " WHERE " + " AND ".join(where_conditions)
                query += where_clause
                count_query += where_clause
            query += " ORDER BY date DESC, created_at DESC"
            query += " LIMIT ? OFFSET ?"
            params.extend([per_page, offset])
            total_result = await podcasts_db.execute_query(count_query, tuple(params[:-2] if params else ()), fetch=True, fetch_one=True)
            total_items = total_result.get("count", 0) if total_result else 0
            total_pages = math.ceil(total_items / per_page) if total_items > 0 else 0
            podcasts = await podcasts_db.execute_query(query, tuple(params), fetch=True)
            for podcast in podcasts:
                podcast["audio_generated"] = bool(podcast.get("audio_generated", 0))
                if podcast.get("banner_img_path"):
                    podcast["banner_img"] = podcast.get("banner_img_path")
                else:
                    podcast["banner_img"] = None
                podcast.pop("banner_img_path", None)
                podcast["identifier"] = str(podcast.get("id", ""))
            has_next = page < total_pages
            has_prev = page > 1
            return {
                "items": podcasts,
                "total": total_items,
                "page": page,
                "per_page": per_page,
                "total_pages": total_pages,
                "has_next": has_next,
                "has_prev": has_prev,
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error loading podcasts: {str(e)}")
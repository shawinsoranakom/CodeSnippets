def update_podcast_config(db_path: str, config_id: int, updates: Dict[str, Any]) -> bool:
    conn = sqlite3.connect(db_path)
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM podcast_configs WHERE id = ?", (config_id,))
        if not cursor.fetchone():
            return False
        if not updates:
            return True
        set_clauses = []
        params = []
        set_clauses.append("updated_at = ?")
        params.append(datetime.now().isoformat())
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
        for field, value in updates.items():
            if field in allowed_fields:
                if field == "is_active":
                    value = 1 if value else 0
                set_clauses.append(f"{field} = ?")
                params.append(value)
        params.append(config_id)
        query = f"""
        UPDATE podcast_configs
        SET {", ".join(set_clauses)}
        WHERE id = ?
        """
        cursor.execute(query, tuple(params))
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        print(f"Error updating podcast config: {e}")
        return False
    finally:
        conn.close()
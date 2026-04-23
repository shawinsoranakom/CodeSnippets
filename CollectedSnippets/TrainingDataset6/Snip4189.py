def get_db():
        call_counter["count"] += 1
        return f"db_{call_counter['count']}"
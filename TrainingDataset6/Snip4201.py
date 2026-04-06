def get_db_session():
        call_counts["get_db_session"] += 1
        return f"db_session_{call_counts['get_db_session']}"
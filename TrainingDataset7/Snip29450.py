def default_text_search_config(self):
        with connection.cursor() as cursor:
            cursor.execute("SHOW default_text_search_config")
            row = cursor.fetchone()
            return row[0] if row else None
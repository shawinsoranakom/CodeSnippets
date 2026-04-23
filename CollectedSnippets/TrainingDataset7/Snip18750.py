def constraint_checks_enabled():
            with connection.cursor() as cursor:
                return bool(cursor.execute("PRAGMA foreign_keys").fetchone()[0])
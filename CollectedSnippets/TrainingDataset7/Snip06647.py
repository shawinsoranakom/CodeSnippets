def prepare_database(self):
        super().prepare_database()
        # Check that postgis extension is installed.
        with self.cursor() as cursor:
            cursor.execute("SELECT 1 FROM pg_extension WHERE extname = %s", ["postgis"])
            if bool(cursor.fetchone()):
                return
            cursor.execute("CREATE EXTENSION IF NOT EXISTS postgis")
            if is_psycopg3:
                # Ensure adapters are registers if PostGIS is used within this
                # connection.
                self.register_geometry_adapters(self.connection, True)
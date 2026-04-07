def prepare_database(self):
        super().prepare_database()
        # Check if spatial metadata have been initialized in the database
        with self.cursor() as cursor:
            cursor.execute("PRAGMA table_info(geometry_columns);")
            if cursor.fetchall() == []:
                if self.ops.spatial_version < (5,):
                    cursor.execute("SELECT InitSpatialMetaData(1)")
                else:
                    cursor.execute("SELECT InitSpatialMetaDataFull(1)")
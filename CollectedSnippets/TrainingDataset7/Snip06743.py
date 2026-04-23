def add_field(self, model, field):
        from django.contrib.gis.db.models import GeometryField

        if isinstance(field, GeometryField):
            # Populate self.geometry_sql
            self.column_sql(model, field)
            for sql in self.geometry_sql:
                self.execute(sql)
            self.geometry_sql = []
        else:
            super().add_field(model, field)
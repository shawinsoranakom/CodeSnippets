def remove_field(self, model, field):
        from django.contrib.gis.db.models import GeometryField

        # NOTE: If the field is a geometry field, the table is just recreated,
        # the parent's remove_field can't be used cause it will skip the
        # recreation if the field does not have a database type. Geometry
        # fields do not have a db type cause they are added and removed via
        # stored procedures.
        if isinstance(field, GeometryField):
            self._remake_table(model, delete_field=field)
        else:
            super().remove_field(model, field)
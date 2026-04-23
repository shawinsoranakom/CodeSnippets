def geometry_columns(self):
        from django.contrib.gis.db.backends.oracle.models import OracleGeometryColumns

        return OracleGeometryColumns
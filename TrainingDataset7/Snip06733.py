def geometry_columns(self):
        from django.contrib.gis.db.backends.spatialite.models import (
            SpatialiteGeometryColumns,
        )

        return SpatialiteGeometryColumns
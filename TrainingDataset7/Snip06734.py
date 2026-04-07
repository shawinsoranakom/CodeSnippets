def spatial_ref_sys(self):
        from django.contrib.gis.db.backends.spatialite.models import (
            SpatialiteSpatialRefSys,
        )

        return SpatialiteSpatialRefSys
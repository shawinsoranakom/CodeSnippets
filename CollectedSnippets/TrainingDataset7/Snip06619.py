def spatial_ref_sys(self):
        from django.contrib.gis.db.backends.oracle.models import OracleSpatialRefSys

        return OracleSpatialRefSys
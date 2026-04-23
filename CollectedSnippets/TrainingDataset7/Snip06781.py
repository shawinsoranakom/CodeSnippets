def get_transform(self, name):
        from django.contrib.gis.db.models.lookups import RasterBandTransform

        try:
            band_index = int(name)
            return type(
                "SpecificRasterBandTransform",
                (RasterBandTransform,),
                {"band_index": band_index},
            )
        except ValueError:
            pass
        return super().get_transform(name)
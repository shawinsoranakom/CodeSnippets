def transform(
        self, srs, driver=None, name=None, resampling="NearestNeighbour", max_error=0.0
    ):
        """
        Return a copy of this raster reprojected into the given spatial
        reference system.
        """
        # Convert the resampling algorithm name into an algorithm id
        algorithm = GDAL_RESAMPLE_ALGORITHMS[resampling]

        if isinstance(srs, SpatialReference):
            target_srs = srs
        elif isinstance(srs, (int, str)):
            target_srs = SpatialReference(srs)
        else:
            raise TypeError(
                "Transform only accepts SpatialReference, string, and integer "
                "objects."
            )

        if target_srs.srid == self.srid and (not driver or driver == self.driver.name):
            return self.clone(name)
        # Create warped virtual dataset in the target reference system
        target = capi.auto_create_warped_vrt(
            self._ptr,
            self.srs.wkt.encode(),
            target_srs.wkt.encode(),
            algorithm,
            max_error,
            c_void_p(),
        )
        target = GDALRaster(target)

        # Construct the target warp dictionary from the virtual raster
        data = {
            "srid": target_srs.srid,
            "width": target.width,
            "height": target.height,
            "origin": [target.origin.x, target.origin.y],
            "scale": [target.scale.x, target.scale.y],
            "skew": [target.skew.x, target.skew.y],
        }

        # Set the driver and filepath if provided
        if driver:
            data["driver"] = driver

        if name:
            data["name"] = name

        # Warp the raster into new srid
        return self.warp(data, resampling=resampling, max_error=max_error)
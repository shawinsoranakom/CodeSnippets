def warp(self, ds_input, resampling="NearestNeighbour", max_error=0.0):
        """
        Return a warped GDALRaster with the given input characteristics.

        The input is expected to be a dictionary containing the parameters
        of the target raster. Allowed values are width, height, SRID, origin,
        scale, skew, datatype, driver, and name (filename).

        By default, the warp functions keeps all parameters equal to the values
        of the original source raster. For the name of the target raster, the
        name of the source raster will be used and appended with
        _copy. + source_driver_name.

        In addition, the resampling algorithm can be specified with the
        "resampling" input parameter. The default is NearestNeighbor. For a
        list of all options consult the GDAL_RESAMPLE_ALGORITHMS constant.
        """
        # Get the parameters defining the geotransform, srid, and size of the
        # raster
        ds_input.setdefault("width", self.width)
        ds_input.setdefault("height", self.height)
        ds_input.setdefault("srid", self.srs.srid)
        ds_input.setdefault("origin", self.origin)
        ds_input.setdefault("scale", self.scale)
        ds_input.setdefault("skew", self.skew)
        # Get the driver, name, and datatype of the target raster
        ds_input.setdefault("driver", self.driver.name)

        if "name" not in ds_input:
            ds_input["name"] = self.name + "_copy." + self.driver.name

        if "datatype" not in ds_input:
            ds_input["datatype"] = self.bands[0].datatype()

        # Instantiate raster bands filled with nodata values.
        ds_input["bands"] = [{"nodata_value": bnd.nodata_value} for bnd in self.bands]

        # Create target raster
        target = GDALRaster(ds_input, write=True)

        # Select resampling algorithm
        algorithm = GDAL_RESAMPLE_ALGORITHMS[resampling]

        # Reproject image
        capi.reproject_image(
            self._ptr,
            self.srs.wkt.encode(),
            target._ptr,
            target.srs.wkt.encode(),
            algorithm,
            0.0,
            max_error,
            c_void_p(),
            c_void_p(),
            c_void_p(),
        )

        # Make sure all data is written to file
        target._flush()

        return target
def __init__(self, ds_input, ds_driver=False, write=False, encoding="utf-8"):
        # The write flag.
        self._write = capi.GDAL_OF_UPDATE if write else capi.GDAL_OF_READONLY
        # See also https://gdal.org/development/rfc/rfc23_ogr_unicode.html
        self.encoding = encoding

        Driver.ensure_registered()

        if isinstance(ds_input, (str, Path)):
            try:
                # GDALOpenEx will auto-detect the data source type.
                ds = capi.open_ds(
                    force_bytes(ds_input),
                    self._write | capi.GDAL_OF_VECTOR,
                    None,
                    None,
                    None,
                )
            except GDALException:
                # Making the error message more clear rather than something
                # like "Invalid pointer returned from OGROpen".
                raise GDALException('Could not open the datasource at "%s"' % ds_input)
        elif isinstance(ds_input, self.ptr_type) and isinstance(
            ds_driver, Driver.ptr_type
        ):
            ds = ds_input
        else:
            raise GDALException("Invalid data source input type: %s" % type(ds_input))

        if ds:
            self.ptr = ds
            driver = capi.get_dataset_driver(ds)
            self.driver = Driver(driver)
        else:
            # Raise an exception if the returned pointer is NULL
            raise GDALException('Invalid data source file "%s"' % ds_input)
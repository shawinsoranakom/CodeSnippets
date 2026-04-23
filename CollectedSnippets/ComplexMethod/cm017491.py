def __init__(self, ds_input, write=False):
        self._write = 1 if write else 0
        Driver.ensure_registered()

        # Preprocess json inputs. This converts json strings to dictionaries,
        # which are parsed below the same way as direct dictionary inputs.
        if isinstance(ds_input, str) and json_regex.match(ds_input):
            ds_input = json.loads(ds_input)

        # If input is a valid file path, try setting file as source.
        if isinstance(ds_input, (str, Path)):
            ds_input = str(ds_input)
            if not ds_input.startswith(VSI_FILESYSTEM_PREFIX) and not os.path.exists(
                ds_input
            ):
                raise GDALException(
                    'Unable to read raster source input "%s".' % ds_input
                )
            try:
                # GDALOpen will auto-detect the data source type.
                self._ptr = capi.open_ds(force_bytes(ds_input), self._write)
            except GDALException as err:
                raise GDALException(
                    'Could not open the datasource at "{}" ({}).'.format(ds_input, err)
                )
        elif isinstance(ds_input, bytes):
            # Create a new raster in write mode.
            self._write = 1
            # Get size of buffer.
            size = sys.getsizeof(ds_input)
            # Pass data to ctypes, keeping a reference to the ctypes object so
            # that the vsimem file remains available until the GDALRaster is
            # deleted.
            self._ds_input = c_buffer(ds_input)
            # Create random name to reference in vsimem filesystem.
            vsi_path = os.path.join(VSI_MEM_FILESYSTEM_BASE_PATH, str(uuid.uuid4()))
            # Create vsimem file from buffer.
            capi.create_vsi_file_from_mem_buffer(
                force_bytes(vsi_path),
                byref(self._ds_input),
                size,
                VSI_TAKE_BUFFER_OWNERSHIP,
            )
            # Open the new vsimem file as a GDALRaster.
            try:
                self._ptr = capi.open_ds(force_bytes(vsi_path), self._write)
            except GDALException:
                # Remove the broken file from the VSI filesystem.
                capi.unlink_vsi_file(force_bytes(vsi_path))
                raise GDALException("Failed creating VSI raster from the input buffer.")
        elif isinstance(ds_input, dict):
            # A new raster needs to be created in write mode
            self._write = 1

            # Create driver (in memory by default)
            driver = Driver(ds_input.get("driver", "MEM"))

            # For out of memory drivers, check filename argument
            if driver.name != "MEM" and "name" not in ds_input:
                raise GDALException(
                    'Specify name for creation of raster with driver "{}".'.format(
                        driver.name
                    )
                )

            # Check if width and height where specified
            if "width" not in ds_input or "height" not in ds_input:
                raise GDALException(
                    "Specify width and height attributes for JSON or dict input."
                )

            # Check if srid was specified
            if "srid" not in ds_input:
                raise GDALException("Specify srid for JSON or dict input.")

            # Create null terminated gdal options array.
            papsz_options = []
            for key, val in ds_input.get("papsz_options", {}).items():
                option = "{}={}".format(key, val)
                papsz_options.append(option.upper().encode())
            papsz_options.append(None)

            # Convert papszlist to ctypes array.
            papsz_options = (c_char_p * len(papsz_options))(*papsz_options)

            # Create GDAL Raster
            self._ptr = capi.create_ds(
                driver._ptr,
                force_bytes(ds_input.get("name", "")),
                ds_input["width"],
                ds_input["height"],
                ds_input.get("nr_of_bands", len(ds_input.get("bands", []))),
                ds_input.get("datatype", 6),
                byref(papsz_options),
            )

            # Set band data if provided
            for i, band_input in enumerate(ds_input.get("bands", [])):
                band = self.bands[i]
                if "nodata_value" in band_input:
                    band.nodata_value = band_input["nodata_value"]
                    # Instantiate band filled with nodata values if only
                    # partial input data has been provided.
                    if band.nodata_value is not None and (
                        "data" not in band_input
                        or "size" in band_input
                        or "shape" in band_input
                    ):
                        band.data(data=(band.nodata_value,), shape=(1, 1))
                # Set band data values from input.
                band.data(
                    data=band_input.get("data"),
                    size=band_input.get("size"),
                    shape=band_input.get("shape"),
                    offset=band_input.get("offset"),
                )

            # Set SRID
            self.srs = ds_input.get("srid")

            # Set additional properties if provided
            if "origin" in ds_input:
                self.origin.x, self.origin.y = ds_input["origin"]

            if "scale" in ds_input:
                self.scale.x, self.scale.y = ds_input["scale"]

            if "skew" in ds_input:
                self.skew.x, self.skew.y = ds_input["skew"]
        elif isinstance(ds_input, c_void_p):
            # Instantiate the object using an existing pointer to a gdal
            # raster.
            self._ptr = ds_input
        else:
            raise GDALException(
                'Invalid data source input type: "{}".'.format(type(ds_input))
            )
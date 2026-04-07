def handle(self, *args, **options):
        data_source, model_name = options.pop("data_source"), options.pop("model_name")

        # Getting the OGR DataSource from the string parameter.
        try:
            ds = gdal.DataSource(data_source)
        except gdal.GDALException as msg:
            raise CommandError(msg)

        # Returning the output of ogrinspect with the given arguments
        # and options.
        from django.contrib.gis.utils.ogrinspect import _ogrinspect, mapping

        # Filter options to params accepted by `_ogrinspect`
        ogr_options = {
            k: v
            for k, v in options.items()
            if k in get_func_args(_ogrinspect) and v is not None
        }
        output = [s for s in _ogrinspect(ds, model_name, **ogr_options)]

        if options["mapping"]:
            # Constructing the keyword arguments for `mapping`, and
            # calling it on the data source.
            kwargs = {
                "geom_name": options["geom_name"],
                "layer_key": options["layer_key"],
                "multi_geom": options["multi_geom"],
            }
            mapping_dict = mapping(ds, **kwargs)
            # This extra legwork is so that the dictionary definition comes
            # out in the same order as the fields in the model definition.
            rev_mapping = {v: k for k, v in mapping_dict.items()}
            output.extend(
                [
                    "",
                    "",
                    "# Auto-generated `LayerMapping` dictionary for %s model"
                    % model_name,
                    "%s_mapping = {" % model_name.lower(),
                ]
            )
            output.extend(
                "    '%s': '%s'," % (rev_mapping[ogr_fld], ogr_fld)
                for ogr_fld in ds[options["layer_key"]].fields
            )
            output.extend(
                [
                    "    '%s': '%s',"
                    % (options["geom_name"], mapping_dict[options["geom_name"]]),
                    "}",
                ]
            )
        return "\n".join(output)
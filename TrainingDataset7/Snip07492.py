def add_arguments(self, parser):
        parser.add_argument("data_source", help="Path to the data source.")
        parser.add_argument("model_name", help="Name of the model to create.")
        parser.add_argument(
            "--blank",
            action=ListOptionAction,
            default=False,
            help="Use a comma separated list of OGR field names to add "
            "the `blank=True` option to the field definition. Set to `true` "
            "to apply to all applicable fields.",
        )
        parser.add_argument(
            "--decimal",
            action=ListOptionAction,
            default=False,
            help="Use a comma separated list of OGR float fields to "
            "generate `DecimalField` instead of the default "
            "`FloatField`. Set to `true` to apply to all OGR float fields.",
        )
        parser.add_argument(
            "--geom-name",
            default="geom",
            help="Specifies the model name for the Geometry Field (defaults to `geom`)",
        )
        parser.add_argument(
            "--layer",
            dest="layer_key",
            action=LayerOptionAction,
            default=0,
            help="The key for specifying which layer in the OGR data "
            "source to use. Defaults to 0 (the first layer). May be "
            "an integer or a string identifier for the layer.",
        )
        parser.add_argument(
            "--multi-geom",
            action="store_true",
            help="Treat the geometry in the data source as a geometry collection.",
        )
        parser.add_argument(
            "--name-field",
            help="Specifies a field name to return for the __str__() method.",
        )
        parser.add_argument(
            "--no-imports",
            action="store_false",
            dest="imports",
            help="Do not include `from django.contrib.gis.db import models` statement.",
        )
        parser.add_argument(
            "--null",
            action=ListOptionAction,
            default=False,
            help="Use a comma separated list of OGR field names to add "
            "the `null=True` option to the field definition. Set to `true` "
            "to apply to all applicable fields.",
        )
        parser.add_argument(
            "--srid",
            help="The SRID to use for the Geometry Field. If it can be "
            "determined, the SRID of the data source is used.",
        )
        parser.add_argument(
            "--mapping",
            action="store_true",
            help="Generate mapping dictionary for use with `LayerMapping`.",
        )
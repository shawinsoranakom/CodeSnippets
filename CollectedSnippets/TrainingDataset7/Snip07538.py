def __init__(
        self,
        model,
        data,
        mapping,
        layer=0,
        source_srs=None,
        encoding="utf-8",
        transaction_mode="commit_on_success",
        transform=True,
        unique=None,
        using=None,
    ):
        """
        A LayerMapping object is initialized using the given Model (not an
        instance), a DataSource (or string path to an OGR-supported data file),
        and a mapping dictionary. See the module level docstring for more
        details and keyword argument usage.
        """
        # Getting the DataSource and the associated Layer.
        if isinstance(data, (str, Path)):
            self.ds = DataSource(data, encoding=encoding)
        else:
            self.ds = data
        self.layer = self.ds[layer]

        self.using = using if using is not None else router.db_for_write(model)
        connection = connections[self.using]
        self.spatial_backend = connection.ops

        # Setting the mapping & model attributes.
        self.mapping = mapping
        self.model = model

        # Checking the layer -- initialization of the object will fail if
        # things don't check out before hand.
        self.check_layer()

        # Getting the geometry column associated with the model (an
        # exception will be raised if there is no geometry column).
        if connection.features.supports_transform:
            self.geo_field = self.geometry_field()
        else:
            transform = False

        # Checking the source spatial reference system, and getting
        # the coordinate transformation object (unless the `transform`
        # keyword is set to False)
        if transform:
            self.source_srs = self.check_srs(source_srs)
            self.transform = self.coord_transform()
        else:
            self.transform = transform

        # Setting the encoding for OFTString fields, if specified.
        if encoding:
            # Making sure the encoding exists, if not a LookupError
            # exception will be thrown.
            from codecs import lookup

            lookup(encoding)
            self.encoding = encoding
        else:
            self.encoding = None

        if unique:
            self.check_unique(unique)
            transaction_mode = "autocommit"  # Has to be set to autocommit.
            self.unique = unique
        else:
            self.unique = None

        # Setting the transaction decorator with the function in the
        # transaction modes dictionary.
        self.transaction_mode = transaction_mode
        if transaction_mode == "autocommit":
            self.transaction_decorator = None
        elif transaction_mode == "commit_on_success":
            self.transaction_decorator = transaction.atomic
        else:
            raise LayerMapError("Unrecognized transaction mode: %s" % transaction_mode)
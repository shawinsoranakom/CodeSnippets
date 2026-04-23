def __init__(
        self, object_list, *, using=DEFAULT_DB_ALIAS, ignorenonexistent=False, **options
    ):
        super().__init__(object_list, **options)
        self.handle_forward_references = options.pop("handle_forward_references", False)
        self.using = using
        self.ignorenonexistent = ignorenonexistent
        self.field_names_cache = {}  # Model: <list of field_names>
        self._iterator = None
def __init__(
        self,
        file,
        field_name,
        name,
        content_type,
        size,
        charset,
        content_type_extra=None,
    ):
        super().__init__(file, name, content_type, size, charset, content_type_extra)
        self.field_name = field_name
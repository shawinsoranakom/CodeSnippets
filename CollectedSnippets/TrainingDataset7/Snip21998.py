def new_file(
        self,
        field_name,
        file_name,
        content_type,
        content_length,
        charset=None,
        content_type_extra=None,
    ):
        super().new_file(
            file_name,
            file_name,
            content_length,
            content_length,
            charset,
            content_type_extra,
        )
        self.file = NamedTemporaryFile(suffix=".upload", dir=self.upload_dir)
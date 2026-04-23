def __init__(self, name, content_type, size, charset, content_type_extra=None):
        _, ext = os.path.splitext(name)
        file = tempfile.NamedTemporaryFile(
            suffix=".upload" + ext, dir=settings.FILE_UPLOAD_TEMP_DIR
        )
        super().__init__(file, name, content_type, size, charset, content_type_extra)
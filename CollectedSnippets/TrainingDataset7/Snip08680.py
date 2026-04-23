def attach_file(self, path, mimetype=None):
        """
        Attach a file from the filesystem.

        Set the mimetype to DEFAULT_ATTACHMENT_MIME_TYPE if it isn't specified
        and cannot be guessed.

        For a text/* mimetype (guessed or specified), decode the file's content
        as UTF-8. If that fails, set the mimetype to
        DEFAULT_ATTACHMENT_MIME_TYPE and don't decode the content.
        """
        path = Path(path)
        with path.open("rb") as file:
            content = file.read()
            self.attach(path.name, content, mimetype)
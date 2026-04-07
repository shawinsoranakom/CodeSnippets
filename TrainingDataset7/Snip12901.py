def multipart_parser_class(self, multipart_parser_class):
        if hasattr(self, "_files"):
            raise RuntimeError(
                "You cannot set the multipart parser class after the upload has been "
                "processed."
            )
        self._multipart_parser_class = multipart_parser_class
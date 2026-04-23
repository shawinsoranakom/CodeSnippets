def _load_post_and_files(self):
        """
        Populate self._post and self._files if the content-type is a form type
        """
        if self.method != "POST":
            self._post, self._files = (
                QueryDict(encoding=self._encoding),
                MultiValueDict(),
            )
            return
        if self._read_started and not hasattr(self, "_body"):
            self._mark_post_parse_error()
            return

        if self.content_type == "multipart/form-data":
            if hasattr(self, "_body"):
                # Use already read data
                data = BytesIO(self._body)
            else:
                data = self
            try:
                self._post, self._files = self.parse_file_upload(self.META, data)
            except (MultiPartParserError, TooManyFilesSent):
                # An error occurred while parsing POST data. Since when
                # formatting the error the request handler might access
                # self.POST, set self._post and self._file to prevent
                # attempts to parse POST data again.
                self._mark_post_parse_error()
                raise
        elif self.content_type == "application/x-www-form-urlencoded":
            # According to RFC 1866, the "application/x-www-form-urlencoded"
            # content type does not have a charset and should be always treated
            # as UTF-8.
            if self._encoding is not None and self._encoding.lower() != "utf-8":
                raise BadRequest(
                    "HTTP requests with the 'application/x-www-form-urlencoded' "
                    "content type must be UTF-8 encoded."
                )
            self._post = QueryDict(self.body, encoding="utf-8")
            self._files = MultiValueDict()
        else:
            self._post, self._files = (
                QueryDict(encoding=self._encoding),
                MultiValueDict(),
            )
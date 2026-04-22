def set_extra_headers(self, path: str) -> None:
        """Add Content-Disposition header for downloadable files.

        Set header value to "attachment" indicating that file should be saved
        locally instead of displaying inline in browser.

        We also set filename to specify the filename for downloaded files.
        Used for serving downloadable files, like files stored via the
        `st.download_button` widget.
        """
        media_file = self._storage.get_file(path)

        if media_file and media_file.kind == MediaFileKind.DOWNLOADABLE:
            filename = media_file.filename

            if not filename:
                title = self.get_argument("title", "", True)
                title = unquote_plus(title)
                filename = generate_download_filename_from_title(title)
                filename = (
                    f"{filename}{get_extension_for_mimetype(media_file.mimetype)}"
                )

            try:
                # Check that the value can be encoded in latin1. Latin1 is
                # the default encoding for headers.
                filename.encode("latin1")
                file_expr = 'filename="{}"'.format(filename)
            except UnicodeEncodeError:
                # RFC5987 syntax.
                # See: https://datatracker.ietf.org/doc/html/rfc5987
                file_expr = "filename*=utf-8''{}".format(quote(filename))

            self.set_header("Content-Disposition", f"attachment; {file_expr}")
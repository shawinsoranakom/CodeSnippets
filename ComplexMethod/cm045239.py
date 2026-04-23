def _open_path(
        self,
        path: str,
    ) -> None:
        """Open a file for reading, converting it to Markdown in the process.

        Arguments:
            path: The path of the file or directory to open.
        """

        if not self._validate_path(path):
            # Not robust to TOCTOU issues.
            # Mitigate by running with limited permissions, or use a sandbox.
            self.page_title = "FileNotFoundError"
            self._set_page_content(f"# FileNotFoundError\n\nFile not found: {path}")
        else:
            try:
                if os.path.isdir(path):  # TODO: Fix markdown_converter types
                    res = self._markdown_converter.convert_stream(  # type: ignore
                        io.BytesIO(self._fetch_local_dir(path).encode("utf-8")), file_extension=".txt"
                    )
                    assert self._validate_path(path)
                    self.page_title = res.title
                    self._set_page_content(res.text_content, split_pages=False)
                else:
                    res = self._markdown_converter.convert_local(path)
                    assert self._validate_path(path)
                    self.page_title = res.title
                    self._set_page_content(res.text_content)
            except UnsupportedFormatException:
                self.page_title = "UnsupportedFormatException"
                self._set_page_content(f"# UnsupportedFormatException\n\nCannot preview '{path}' as Markdown.")
            except FileConversionException:
                self.page_title = "FileConversionException."
                self._set_page_content(f"# FileConversionException\n\nError converting '{path}' to Markdown.")
            except FileNotFoundError:
                self.page_title = "FileNotFoundError"
                self._set_page_content(f"# FileNotFoundError\n\nFile not found: {path}")
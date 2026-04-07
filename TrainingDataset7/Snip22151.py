def _dumpdata_assert(
        self,
        args,
        output,
        format="json",
        filename=None,
        natural_foreign_keys=False,
        natural_primary_keys=False,
        use_base_manager=False,
        exclude_list=[],
        primary_keys="",
    ):
        new_io = StringIO()
        filename = filename and os.path.join(tempfile.gettempdir(), filename)
        management.call_command(
            "dumpdata",
            *args,
            format=format,
            stdout=new_io,
            stderr=new_io,
            output=filename,
            use_natural_foreign_keys=natural_foreign_keys,
            use_natural_primary_keys=natural_primary_keys,
            use_base_manager=use_base_manager,
            exclude=exclude_list,
            primary_keys=primary_keys,
        )
        if filename:
            file_root, file_ext = os.path.splitext(filename)
            compression_formats = {
                ".bz2": (open, file_root),
                ".gz": (gzip.open, filename),
                ".lzma": (open, file_root),
                ".xz": (open, file_root),
                ".zip": (open, file_root),
            }
            if HAS_BZ2:
                compression_formats[".bz2"] = (bz2.open, filename)
            if HAS_LZMA:
                compression_formats[".lzma"] = (lzma.open, filename)
                compression_formats[".xz"] = (lzma.open, filename)
            try:
                open_method, file_path = compression_formats[file_ext]
            except KeyError:
                open_method, file_path = open, filename
            with open_method(file_path, "rt") as f:
                command_output = f.read()
            os.remove(file_path)
        else:
            command_output = new_io.getvalue().strip()
        if format == "json":
            self.assertJSONEqual(command_output, output)
        elif format == "xml":
            self.assertXMLEqual(command_output, output)
        else:
            self.assertEqual(command_output, output)
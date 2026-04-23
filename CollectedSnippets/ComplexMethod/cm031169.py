def _get_writer(file_or_filename, encoding):
    # returns text write method and release all resources after using
    try:
        write = file_or_filename.write
    except AttributeError:
        # file_or_filename is a file name
        if encoding.lower() == "unicode":
            encoding="utf-8"
        with open(file_or_filename, "w", encoding=encoding,
                  errors="xmlcharrefreplace") as file:
            yield file.write, encoding
    else:
        # file_or_filename is a file-like object
        # encoding determines if it is a text or binary writer
        if encoding.lower() == "unicode":
            # use a text writer as is
            yield write, getattr(file_or_filename, "encoding", None) or "utf-8"
        else:
            # wrap a binary writer with TextIOWrapper
            with contextlib.ExitStack() as stack:
                if isinstance(file_or_filename, io.BufferedIOBase):
                    file = file_or_filename
                elif isinstance(file_or_filename, io.RawIOBase):
                    file = io.BufferedWriter(file_or_filename)
                    # Keep the original file open when the BufferedWriter is
                    # destroyed
                    stack.callback(file.detach)
                else:
                    # This is to handle passed objects that aren't in the
                    # IOBase hierarchy, but just have a write method
                    file = io.BufferedIOBase()
                    file.writable = lambda: True
                    file.write = write
                    try:
                        # TextIOWrapper uses this methods to determine
                        # if BOM (for UTF-16, etc) should be added
                        file.seekable = file_or_filename.seekable
                        file.tell = file_or_filename.tell
                    except AttributeError:
                        pass
                file = io.TextIOWrapper(file,
                                        encoding=encoding,
                                        errors="xmlcharrefreplace",
                                        newline="\n")
                # Keep the original file open when the TextIOWrapper is
                # destroyed
                stack.callback(file.detach)
                yield file.write, encoding
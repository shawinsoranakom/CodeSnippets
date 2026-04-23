def write(self, file_or_filename,
              encoding=None,
              xml_declaration=None,
              default_namespace=None,
              method=None, *,
              short_empty_elements=True):
        """Write element tree to a file as XML.

        Arguments:
          *file_or_filename* -- file name or a file object opened for writing

          *encoding* -- the output encoding (default: US-ASCII)

          *xml_declaration* -- bool indicating if an XML declaration should be
                               added to the output. If None, an XML declaration
                               is added if encoding IS NOT either of:
                               US-ASCII, UTF-8, or Unicode

          *default_namespace* -- sets the default XML namespace (for "xmlns")

          *method* -- either "xml" (default), "html, "text", or "c14n"

          *short_empty_elements* -- controls the formatting of elements
                                    that contain no content. If True (default)
                                    they are emitted as a single self-closed
                                    tag, otherwise they are emitted as a pair
                                    of start/end tags

        """
        if self._root is None:
            raise TypeError('ElementTree not initialized')
        if not method:
            method = "xml"
        elif method not in _serialize:
            raise ValueError("unknown method %r" % method)
        if not encoding:
            if method == "c14n":
                encoding = "utf-8"
            else:
                encoding = "us-ascii"
        with _get_writer(file_or_filename, encoding) as (write, declared_encoding):
            if method == "xml" and (xml_declaration or
                    (xml_declaration is None and
                     encoding.lower() != "unicode" and
                     declared_encoding.lower() not in ("utf-8", "us-ascii"))):
                write("<?xml version='1.0' encoding='%s'?>\n" % (
                    declared_encoding,))
            if method == "text":
                _serialize_text(write, self._root)
            else:
                qnames, namespaces = _namespaces(self._root, default_namespace)
                serialize = _serialize[method]
                serialize(write, self._root, qnames, namespaces,
                          short_empty_elements=short_empty_elements)
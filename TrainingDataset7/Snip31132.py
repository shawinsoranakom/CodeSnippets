def wsgi_str(path_info, encoding="utf-8"):
            path_info = path_info.encode(
                encoding
            )  # Actual URL sent by the browser (bytestring)
            path_info = path_info.decode(
                "iso-8859-1"
            )  # Value in the WSGI environ dict (native string)
            return path_info
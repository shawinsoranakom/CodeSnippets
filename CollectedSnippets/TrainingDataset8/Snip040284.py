def _open_read(m, payload):
            is_binary = False
            args, kwargs = m.call_args
            if len(args) > 1:
                if "b" in args[1]:
                    is_binary = True
            encoding = "utf-8"
            if "encoding" in kwargs:
                encoding = kwargs["encoding"]

            if is_binary:
                from io import BytesIO

                return BytesIO(payload)
            else:
                from io import TextIOWrapper

                return TextIOWrapper(str(payload, encoding=encoding))
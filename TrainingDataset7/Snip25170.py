def split(self, *args, **kwargs):
                res = str.split(self, *args, **kwargs)
                trans_real._translations["en-YY"] = None
                return res
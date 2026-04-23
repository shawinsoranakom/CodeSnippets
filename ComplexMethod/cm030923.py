def test_longstrings(self):
        # test long strings to check for memory overflow problems
        errors = [ "strict", "ignore", "replace", "xmlcharrefreplace",
                   "backslashreplace", "namereplace"]
        # register the handlers under different names,
        # to prevent the codec from recognizing the name
        for err in errors:
            codecs.register_error("test." + err, codecs.lookup_error(err))
        l = 1000
        errors += [ "test." + err for err in errors ]
        for uni in [ s*l for s in ("x", "\u3042", "a\xe4") ]:
            for enc in ("ascii", "latin-1", "iso-8859-1", "iso-8859-15",
                        "utf-8", "utf-7", "utf-16", "utf-32"):
                for err in errors:
                    try:
                        uni.encode(enc, err)
                    except UnicodeError:
                        pass
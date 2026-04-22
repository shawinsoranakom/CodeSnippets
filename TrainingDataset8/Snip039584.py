def _build_cffi(self, name):
        ffibuilder = cffi.FFI()
        ffibuilder.set_source(
            "cffi_bin._%s" % name,
            r"""
                static int %s(int x)
                {
                    return x + "A";
                }
            """
            % name,
        )

        ffibuilder.cdef("int %s(int);" % name)
        ffibuilder.compile(verbose=True)
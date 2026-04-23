def testAFakeZlib(self):
        #
        # This could cause a stack overflow before: importing zlib.py
        # from a compressed archive would cause zlib to be imported
        # which would find zlib.py in the archive, which would... etc.
        #
        # This test *must* be executed first: it must be the first one
        # to trigger zipimport to import zlib (zipimport caches the
        # zlib.decompress function object, after which the problem being
        # tested here wouldn't be a problem anymore...
        # (Hence the 'A' in the test method name: to make it the first
        # item in a list sorted by name, like
        # unittest.TestLoader.getTestCaseNames() does.)
        #
        # This test fails on platforms on which the zlib module is
        # statically linked, but the problem it tests for can't
        # occur in that case (builtin modules are always found first),
        # so we'll simply skip it then. Bug #765456.
        #
        if self.compression == ZIP_DEFLATED:
            mod_name = "zlib"
            if zipimport._zlib_decompress:  # validate attr name
                # reset the cached import to avoid test order dependencies
                zipimport._zlib_decompress = None  # reset cache
        elif self.compression == ZIP_ZSTANDARD:
            mod_name = "_zstd"
            if zipimport._zstd_decompressor_class:  # validate attr name
                # reset the cached import to avoid test order dependencies
                zipimport._zstd_decompressor_class = None
        else:
            mod_name = "zlib"  # the ZIP_STORED case below

        if mod_name in sys.builtin_module_names:
            self.skipTest(f"{mod_name} is a builtin module")
        if mod_name in sys.modules:
            del sys.modules[mod_name]
        files = {f"{mod_name}.py": test_src}
        try:
            self.doTest(".py", files, mod_name)
        except ImportError:
            if self.compression != ZIP_STORED:
                # Expected - fake compression module can't decompress
                pass
            else:
                self.fail("expected test to not raise ImportError for uncompressed")
        else:
            if self.compression == ZIP_STORED:
                # Expected - no compression needed, so fake module works
                pass
            else:
                self.fail("expected test to raise ImportError for compressed zip with fake compression module")
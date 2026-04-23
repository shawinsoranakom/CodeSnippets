def setUp(self):
        if os_helper.TESTFN_UNENCODABLE:
            self.dir = os_helper.TESTFN_UNENCODABLE
        elif os_helper.TESTFN_NONASCII:
            self.dir = os_helper.TESTFN_NONASCII
        else:
            self.dir = os_helper.TESTFN
        self.bdir = os.fsencode(self.dir)

        bytesfn = []
        def add_filename(fn):
            try:
                fn = os.fsencode(fn)
            except UnicodeEncodeError:
                return
            bytesfn.append(fn)
        add_filename(os_helper.TESTFN_UNICODE)
        if os_helper.TESTFN_UNENCODABLE:
            add_filename(os_helper.TESTFN_UNENCODABLE)
        if os_helper.TESTFN_NONASCII:
            add_filename(os_helper.TESTFN_NONASCII)
        if not bytesfn:
            self.skipTest("couldn't create any non-ascii filename")

        self.unicodefn = set()
        os.mkdir(self.dir)
        try:
            for fn in bytesfn:
                os_helper.create_empty_file(os.path.join(self.bdir, fn))
                fn = os.fsdecode(fn)
                if fn in self.unicodefn:
                    raise ValueError("duplicate filename")
                self.unicodefn.add(fn)
        except:
            shutil.rmtree(self.dir)
            raise
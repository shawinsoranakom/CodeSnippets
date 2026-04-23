def test_basic(self):
        tests = [
            ("", ("", {})),
            (None, ("", {})),
            ("text/plain", ("text/plain", {})),
            ("text/vnd.just.made.this.up ; ", ("text/vnd.just.made.this.up", {})),
            ("text/plain;charset=us-ascii", ("text/plain", {"charset": "us-ascii"})),
            (
                'text/plain ; charset="us-ascii"',
                ("text/plain", {"charset": "us-ascii"}),
            ),
            (
                'text/plain ; charset="us-ascii"; another=opt',
                ("text/plain", {"charset": "us-ascii", "another": "opt"}),
            ),
            (
                'attachment; filename="silly.txt"',
                ("attachment", {"filename": "silly.txt"}),
            ),
            (
                'attachment; filename="strange;name"',
                ("attachment", {"filename": "strange;name"}),
            ),
            (
                'attachment; filename="strange;name";size=123;',
                ("attachment", {"filename": "strange;name", "size": "123"}),
            ),
            (
                'attachment; filename="strange;name";;;;size=123;;;',
                ("attachment", {"filename": "strange;name", "size": "123"}),
            ),
            (
                'form-data; name="files"; filename="fo\\"o;bar"',
                ("form-data", {"name": "files", "filename": 'fo"o;bar'}),
            ),
            (
                'form-data; name="files"; filename="\\"fo\\"o;b\\\\ar\\""',
                ("form-data", {"name": "files", "filename": '"fo"o;b\\ar"'}),
            ),
        ]
        for header, expected in tests:
            with self.subTest(header=header):
                self.assertEqual(parse_header_parameters(header), expected)
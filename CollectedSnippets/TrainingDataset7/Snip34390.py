def test_bytestring(self):
        loader = self.engine.template_loaders[0]
        msg = "Can't mix strings and bytes in path components"
        with self.assertRaisesMessage(TypeError, msg):
            list(loader.get_template_sources(b"\xc3\x85ngstr\xc3\xb6m"))
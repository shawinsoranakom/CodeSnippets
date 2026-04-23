def test_harden_runtime(self):
        msg = (
            "subclasses of BasePasswordHasher should provide a harden_runtime() method"
        )
        with self.assertWarnsMessage(Warning, msg):
            self.hasher.harden_runtime("password", "encoded")
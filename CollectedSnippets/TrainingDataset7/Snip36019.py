def test_common_roots(self):
        paths = (
            Path("/first/second"),
            Path("/first/second/third"),
            Path("/first/"),
            Path("/root/first/"),
        )
        results = autoreload.common_roots(paths)
        self.assertCountEqual(results, [Path("/first/"), Path("/root/first/")])
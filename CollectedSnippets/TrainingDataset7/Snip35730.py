def test_nonmatching_urls(self):
        test_data = (
            ("int", {"-1", "letters"}),
            ("str", {"", "/"}),
            ("path", {""}),
            ("slug", {"", "stars*notallowed"}),
            (
                "uuid",
                {
                    "",
                    "9da9369-838e-4750-91a5-f7805cd82839",
                    "39da9369-838-4750-91a5-f7805cd82839",
                    "39da9369-838e-475-91a5-f7805cd82839",
                    "39da9369-838e-4750-91a-f7805cd82839",
                    "39da9369-838e-4750-91a5-f7805cd8283",
                },
            ),
        )
        for url_name, url_suffixes in test_data:
            for url_suffix in url_suffixes:
                url = "/%s/%s/" % (url_name, url_suffix)
                with self.subTest(url=url), self.assertRaises(Resolver404):
                    resolve(url)
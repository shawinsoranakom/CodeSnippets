def test_patch_cache_control(self):
        tests = (
            # Initial Cache-Control, kwargs to patch_cache_control, expected
            # Cache-Control parts.
            (None, {"private": True}, {"private"}),
            ("", {"private": True}, {"private"}),
            # no-cache.
            ("", {"no_cache": "Set-Cookie"}, {"no-cache=Set-Cookie"}),
            ("", {"no-cache": "Set-Cookie"}, {"no-cache=Set-Cookie"}),
            ("no-cache=Set-Cookie", {"no_cache": True}, {"no-cache"}),
            ("no-cache=Set-Cookie,no-cache=Link", {"no_cache": True}, {"no-cache"}),
            (
                "no-cache=Set-Cookie",
                {"no_cache": "Link"},
                {"no-cache=Set-Cookie", "no-cache=Link"},
            ),
            (
                "no-cache=Set-Cookie,no-cache=Link",
                {"no_cache": "Custom"},
                {"no-cache=Set-Cookie", "no-cache=Link", "no-cache=Custom"},
            ),
            # Test whether private/public attributes are mutually exclusive
            ("private", {"private": True}, {"private"}),
            ("private", {"public": True}, {"public"}),
            ("public", {"public": True}, {"public"}),
            ("public", {"private": True}, {"private"}),
            (
                "must-revalidate,max-age=60,private",
                {"public": True},
                {"must-revalidate", "max-age=60", "public"},
            ),
            (
                "must-revalidate,max-age=60,public",
                {"private": True},
                {"must-revalidate", "max-age=60", "private"},
            ),
            (
                "must-revalidate,max-age=60",
                {"public": True},
                {"must-revalidate", "max-age=60", "public"},
            ),
        )

        cc_delim_re = re.compile(r"\s*,\s*")

        for initial_cc, newheaders, expected_cc in tests:
            with self.subTest(initial_cc=initial_cc, newheaders=newheaders):
                response = HttpResponse()
                if initial_cc is not None:
                    response.headers["Cache-Control"] = initial_cc
                patch_cache_control(response, **newheaders)
                parts = set(cc_delim_re.split(response.headers["Cache-Control"]))
                self.assertEqual(parts, expected_cc)
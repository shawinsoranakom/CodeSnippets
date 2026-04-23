def test_unicode_template_name(self):
        with self.source_checker(["/dir1", "/dir2"]) as check_sources:
            check_sources("Ångström", ["/dir1/Ångström", "/dir2/Ångström"])
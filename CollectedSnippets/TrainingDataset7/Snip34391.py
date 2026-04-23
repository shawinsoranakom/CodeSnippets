def test_unicode_dir_name(self):
        with self.source_checker(["/Straße"]) as check_sources:
            check_sources("Ångström", ["/Straße/Ångström"])
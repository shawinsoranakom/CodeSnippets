def test_save_another(self):
        """
        #17415 - Another site can be created right after the default one.

        On some backends the sequence needs to be reset after saving with an
        explicit ID. There shouldn't be a sequence collisions by saving another
        site. This test is only meaningful with databases that use sequences
        for automatic primary keys such as PostgreSQL and Oracle.
        """
        create_default_site(self.app_config, verbosity=0)
        Site(domain="example2.com", name="example2.com").save()
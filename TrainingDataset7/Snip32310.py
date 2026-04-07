def test_unique_domain(self):
        site = Site(domain=self.site.domain)
        msg = "Site with this Domain name already exists."
        with self.assertRaisesMessage(ValidationError, msg):
            site.validate_unique()
def test_composite_pk_model(self):
        msg = (
            "The model Guest has a composite primary key, so it cannot be registered "
            "with admin."
        )
        with self.assertRaisesMessage(ImproperlyConfigured, msg):
            self.site.register(Guest)
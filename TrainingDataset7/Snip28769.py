def test_get_fields_is_immutable(self):
        msg = IMMUTABLE_WARNING % "get_fields()"
        for _ in range(2):
            # Running unit test twice to ensure both non-cached and cached
            # result are immutable.
            fields = Person._meta.get_fields()
            with self.assertRaisesMessage(AttributeError, msg):
                fields += ["errors"]
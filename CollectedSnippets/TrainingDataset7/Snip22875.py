def test_remove_cached_field(self):
        class TestForm(Form):
            name = CharField(max_length=10)

            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                # Populate fields cache.
                [field for field in self]
                # Removed cached field.
                del self.fields["name"]

        f = TestForm({"name": "abcde"})

        with self.assertRaises(KeyError):
            f["name"]
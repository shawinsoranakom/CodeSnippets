def test_deconstruction_storage_callable_default(self):
        """
        A callable that returns default_storage is not omitted when
        deconstructing.
        """
        obj = Storage()
        *_, kwargs = obj._meta.get_field("storage_callable_default").deconstruct()
        self.assertIs(kwargs["storage"], callable_default_storage)
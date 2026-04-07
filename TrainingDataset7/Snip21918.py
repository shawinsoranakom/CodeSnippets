def test_deconstruction(self):
        """
        Deconstructing gives the original callable, not the evaluated value.
        """
        obj = Storage()
        *_, kwargs = obj._meta.get_field("storage_callable").deconstruct()
        storage = kwargs["storage"]
        self.assertIs(storage, callable_storage)
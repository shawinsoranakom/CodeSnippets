def test_storage_properties(self):
        # Properties of the Storage as described in the ticket.
        storage = DummyStorage()
        self.assertEqual(
            storage.get_modified_time("name"),
            datetime.datetime(1970, 1, 1, tzinfo=datetime.UTC),
        )
        with self.assertRaisesMessage(
            NotImplementedError, "This backend doesn't support absolute paths."
        ):
            storage.path("name")
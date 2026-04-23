def test_unique_errors(self):
        UniqueErrorsModel.objects.create(name="Some Name", no=10)
        m = UniqueErrorsModel(name="Some Name", no=11)
        with self.assertRaises(ValidationError) as cm:
            m.full_clean()
        self.assertEqual(
            cm.exception.message_dict, {"name": ["Custom unique name message."]}
        )

        m = UniqueErrorsModel(name="Some Other Name", no=10)
        with self.assertRaises(ValidationError) as cm:
            m.full_clean()
        self.assertEqual(
            cm.exception.message_dict, {"no": ["Custom unique number message."]}
        )
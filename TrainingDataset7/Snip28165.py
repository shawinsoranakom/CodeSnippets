def test_wrong_value(self):
        with self.assertRaisesMessage(
            exceptions.ValidationError, "is not a valid UUID"
        ):
            UUIDModel.objects.get(field="not-a-uuid")

        with self.assertRaisesMessage(
            exceptions.ValidationError, "is not a valid UUID"
        ):
            UUIDModel.objects.create(field="not-a-uuid")
def test_pk_validated(self):
        with self.assertRaisesMessage(
            exceptions.ValidationError, "is not a valid UUID"
        ):
            PrimaryKeyUUIDModel.objects.get(pk={})

        with self.assertRaisesMessage(
            exceptions.ValidationError, "is not a valid UUID"
        ):
            PrimaryKeyUUIDModel.objects.get(pk=[])
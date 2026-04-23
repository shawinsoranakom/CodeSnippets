def test_unsupported_lookup(self):
        msg = (
            "Unsupported lookup '0_bar' for ArrayField or join on the field not "
            "permitted."
        )
        with self.assertRaisesMessage(FieldError, msg):
            list(NullableIntegerArrayModel.objects.filter(field__0_bar=[2]))

        msg = (
            "Unsupported lookup '0bar' for ArrayField or join on the field not "
            "permitted."
        )
        with self.assertRaisesMessage(FieldError, msg):
            list(NullableIntegerArrayModel.objects.filter(field__0bar=[2]))
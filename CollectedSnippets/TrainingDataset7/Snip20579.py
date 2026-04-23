def test_uuid7_shift_unsupported(self):
        msg = "The shift argument to UUID7 is not supported on this database backend."

        with self.assertRaisesMessage(NotSupportedError, msg):
            UUIDModel.objects.update(uuid=UUID7(shift=timedelta(hours=12)))
def test_timestamp_signer(self):
        value = "hello"
        with freeze_time(123456789):
            signer = signing.TimestampSigner(key="predictable-key")
            ts = signer.sign(value)
            self.assertNotEqual(ts, signing.Signer(key="predictable-key").sign(value))
            self.assertEqual(signer.unsign(ts), value)

        with freeze_time(123456800):
            self.assertEqual(signer.unsign(ts, max_age=12), value)
            # max_age parameter can also accept a datetime.timedelta object
            self.assertEqual(
                signer.unsign(ts, max_age=datetime.timedelta(seconds=11)), value
            )
            with self.assertRaises(signing.SignatureExpired):
                signer.unsign(ts, max_age=10)
def test_uuid7_shift(self):
        shift = timedelta(minutes=1)
        now = datetime.now(timezone.utc)
        m = UUIDModel.objects.create(uuid=UUID7(shift))
        ts = int.from_bytes(m.uuid.bytes[:6])
        uuid_timestamp = datetime.fromtimestamp(ts / 1000, tz=timezone.utc)
        self.assertAlmostEqual(
            (uuid_timestamp - now).total_seconds(), shift.total_seconds(), places=1
        )
def test_uuid7_shift_duration_field(self):
        shift = timedelta(minutes=1)
        m = UUIDModel.objects.create(shift=shift)
        now = datetime.now(timezone.utc)
        UUIDModel.objects.update(uuid=UUID7("shift"))
        m.refresh_from_db()
        ts = int.from_bytes(m.uuid.bytes[:6])
        uuid_timestamp = datetime.fromtimestamp(ts / 1000, tz=timezone.utc)
        self.assertAlmostEqual(
            (uuid_timestamp - now).total_seconds(), shift.total_seconds(), places=1
        )
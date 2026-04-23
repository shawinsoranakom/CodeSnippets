def test_uuid4(self):
        m1 = UUIDModel.objects.create()
        m2 = UUIDModel.objects.create()
        UUIDModel.objects.update(uuid=UUID4())
        m1.refresh_from_db()
        m2.refresh_from_db()
        self.assertIsInstance(m1.uuid, uuid.UUID)
        self.assertEqual(m1.uuid.version, 4)
        self.assertNotEqual(m1.uuid, m2.uuid)
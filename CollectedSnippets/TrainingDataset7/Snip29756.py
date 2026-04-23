def test_random_uuid(self):
        m1 = UUIDTestModel.objects.create()
        m2 = UUIDTestModel.objects.create()
        UUIDTestModel.objects.update(uuid=RandomUUID())
        m1.refresh_from_db()
        m2.refresh_from_db()
        self.assertIsInstance(m1.uuid, uuid.UUID)
        self.assertNotEqual(m1.uuid, m2.uuid)
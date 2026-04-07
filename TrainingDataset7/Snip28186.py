def test_uuid_instance_ok(self):
        field = models.UUIDField()
        field.clean(uuid.uuid4(), None)
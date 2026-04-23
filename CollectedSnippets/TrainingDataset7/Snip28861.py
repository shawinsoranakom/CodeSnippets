def test_primary_key_foreign_key_types(self):
        # Check Department and Worker (non-default PK type)
        d = Department.objects.create(id=10, name="IT")
        w = Worker.objects.create(department=d, name="Full-time")
        self.assertEqual(str(w), "Full-time")
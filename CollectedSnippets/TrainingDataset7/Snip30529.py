def test_unsupported_intersection_raises_db_error(self):
        qs1 = Number.objects.all()
        qs2 = Number.objects.all()
        msg = "intersection is not supported on this database backend"
        with self.assertRaisesMessage(NotSupportedError, msg):
            list(qs1.intersection(qs2))
def test_failure(self):
        msg = "1 != 2 : 1 queries executed, 2 expected\nCaptured queries were:\n1."
        with self.assertRaisesMessage(AssertionError, msg):
            with self.assertNumQueries(2):
                Person.objects.count()

        with self.assertRaises(TypeError):
            with self.assertNumQueries(4000):
                raise TypeError
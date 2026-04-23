def test_ticket10432(self):
        # Testing an empty "__in" filter with a generator as the value.
        def f():
            return iter([])

        n_obj = Note.objects.all()[0]

        def g():
            yield n_obj.pk

        self.assertSequenceEqual(Note.objects.filter(pk__in=f()), [])
        self.assertEqual(list(Note.objects.filter(pk__in=g())), [n_obj])
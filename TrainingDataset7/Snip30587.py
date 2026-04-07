def test_heterogeneous_qs_combination(self):
        # Combining querysets built on different models should behave in a
        # well-defined fashion. We raise an error.
        msg = "Cannot combine queries on two different base models."
        with self.assertRaisesMessage(TypeError, msg):
            Author.objects.all() & Tag.objects.all()
        with self.assertRaisesMessage(TypeError, msg):
            Author.objects.all() | Tag.objects.all()
def test_delete_signals(self):
        data = []

        def pre_delete_handler(signal, sender, instance, origin, **kwargs):
            data.append((instance, sender, instance.id is None, origin))

        # #8285: signals can be any callable
        class PostDeleteHandler:
            def __init__(self, data):
                self.data = data

            def __call__(self, signal, sender, instance, origin, **kwargs):
                self.data.append((instance, sender, instance.id is None, origin))

        post_delete_handler = PostDeleteHandler(data)

        signals.pre_delete.connect(pre_delete_handler, weak=False)
        signals.post_delete.connect(post_delete_handler, weak=False)
        try:
            p1 = Person.objects.create(first_name="John", last_name="Smith")
            p1.delete()
            self.assertEqual(
                data,
                [
                    (p1, Person, False, p1),
                    (p1, Person, False, p1),
                ],
            )
            data[:] = []

            p2 = Person(first_name="James", last_name="Jones")
            p2.id = 99999
            p2.save()
            p2.id = 99998
            p2.save()
            p2.delete()
            self.assertEqual(
                data,
                [
                    (p2, Person, False, p2),
                    (p2, Person, False, p2),
                ],
            )
            data[:] = []

            self.assertQuerySetEqual(
                Person.objects.all(),
                [
                    "James Jones",
                ],
                str,
            )
        finally:
            signals.pre_delete.disconnect(pre_delete_handler)
            signals.post_delete.disconnect(post_delete_handler)
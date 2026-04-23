def test_save_signals(self):
        data = []

        def pre_save_handler(signal, sender, instance, **kwargs):
            data.append((instance, sender, kwargs.get("raw", False)))

        def post_save_handler(signal, sender, instance, **kwargs):
            data.append(
                (instance, sender, kwargs.get("created"), kwargs.get("raw", False))
            )

        signals.pre_save.connect(pre_save_handler, weak=False)
        signals.post_save.connect(post_save_handler, weak=False)
        try:
            p1 = Person.objects.create(first_name="John", last_name="Smith")

            self.assertEqual(
                data,
                [
                    (p1, Person, False),
                    (p1, Person, True, False),
                ],
            )
            data[:] = []

            p1.first_name = "Tom"
            p1.save()
            self.assertEqual(
                data,
                [
                    (p1, Person, False),
                    (p1, Person, False, False),
                ],
            )
            data[:] = []

            # Calling an internal method purely so that we can trigger a "raw"
            # save.
            p1.save_base(raw=True)
            self.assertEqual(
                data,
                [
                    (p1, Person, True),
                    (p1, Person, False, True),
                ],
            )
            data[:] = []

            p2 = Person(first_name="James", last_name="Jones")
            p2.id = 99999
            p2.save()
            self.assertEqual(
                data,
                [
                    (p2, Person, False),
                    (p2, Person, True, False),
                ],
            )
            data[:] = []
            p2.id = 99998
            p2.save()
            self.assertEqual(
                data,
                [
                    (p2, Person, False),
                    (p2, Person, True, False),
                ],
            )

            # The sender should stay the same when using defer().
            data[:] = []
            p3 = Person.objects.defer("first_name").get(pk=p1.pk)
            p3.last_name = "Reese"
            p3.save()
            self.assertEqual(
                data,
                [
                    (p3, Person, False),
                    (p3, Person, False, False),
                ],
            )
        finally:
            signals.pre_save.disconnect(pre_save_handler)
            signals.post_save.disconnect(post_save_handler)
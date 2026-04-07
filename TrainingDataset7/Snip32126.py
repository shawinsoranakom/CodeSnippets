def test_delete_signals_origin_model(self):
        data = []

        def pre_delete_handler(signal, sender, instance, origin, **kwargs):
            data.append((sender, origin))

        def post_delete_handler(signal, sender, instance, origin, **kwargs):
            data.append((sender, origin))

        person = Person.objects.create(first_name="John", last_name="Smith")
        book = Book.objects.create(name="Rayuela")
        Page.objects.create(text="Page 1", book=book)
        Page.objects.create(text="Page 2", book=book)

        signals.pre_delete.connect(pre_delete_handler, weak=False)
        signals.post_delete.connect(post_delete_handler, weak=False)
        try:
            # Instance deletion.
            person.delete()
            self.assertEqual(data, [(Person, person), (Person, person)])
            data[:] = []
            # Cascade deletion.
            book.delete()
            self.assertEqual(
                data,
                [
                    (Page, book),
                    (Page, book),
                    (Book, book),
                    (Page, book),
                    (Page, book),
                    (Book, book),
                ],
            )
        finally:
            signals.pre_delete.disconnect(pre_delete_handler)
            signals.post_delete.disconnect(post_delete_handler)
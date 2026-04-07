def test_deferred_models(self):
        mark_def = Person.objects.using("default").create(name="Mark Pilgrim")
        mark_other = Person.objects.using("other").create(name="Mark Pilgrim")
        orig_b = Book.objects.using("other").create(
            title="Dive into Python",
            published=datetime.date(2009, 5, 4),
            editor=mark_other,
        )
        b = Book.objects.using("other").only("title").get(pk=orig_b.pk)
        self.assertEqual(b.published, datetime.date(2009, 5, 4))
        b = Book.objects.using("other").only("title").get(pk=orig_b.pk)
        b.editor = mark_def
        b.save(using="default")
        self.assertEqual(
            Book.objects.using("default").get(pk=b.pk).published,
            datetime.date(2009, 5, 4),
        )
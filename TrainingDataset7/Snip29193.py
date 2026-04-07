def test_attribute_error_read(self):
        "The AttributeError from AttributeErrorRouter bubbles up"
        b = Book.objects.create(
            title="Pro Django", published=datetime.date(2008, 12, 16)
        )
        with self.override_router():
            with self.assertRaises(AttributeError):
                Book.objects.get(pk=b.pk)
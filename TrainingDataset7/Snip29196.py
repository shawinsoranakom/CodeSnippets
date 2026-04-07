def test_attribute_error_m2m(self):
        "The AttributeError from AttributeErrorRouter bubbles up"
        b = Book.objects.create(
            title="Pro Django", published=datetime.date(2008, 12, 16)
        )
        p = Person.objects.create(name="Marty Alchin")
        with self.override_router():
            with self.assertRaises(AttributeError):
                b.authors.set([p])
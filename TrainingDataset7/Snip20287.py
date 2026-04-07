def test_unicode_pk(self):
        # Primary key may be Unicode string.
        Business.objects.create(name="jaźń")
def test_m2m_with_unicode_reference(self):
        """
        Regression test for #6045: references to other models can be
        strings, providing they are directly convertible to ASCII.
        """
        m1 = StringReferenceModel.objects.create()
        m2 = StringReferenceModel.objects.create()
        m2.others.add(m1)  # used to cause an error (see ticket #6045)
        m2.save()
        list(m2.others.all())
def test_m2m_collection(self):
        b = Book.objects.create(
            title="Pro Django", published=datetime.date(2008, 12, 16)
        )

        p = Person.objects.create(name="Marty Alchin")
        # test add
        b.authors.add(p)
        # test remove
        b.authors.remove(p)
        # test clear
        b.authors.clear()
        # test setattr
        b.authors.set([p])
        # test M2M collection
        b.delete()
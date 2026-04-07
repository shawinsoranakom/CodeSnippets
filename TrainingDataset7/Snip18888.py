def test_autofields_generate_different_values_for_each_instance(self):
        a1 = Article.objects.create(
            headline="First", pub_date=datetime(2005, 7, 30, 0, 0)
        )
        a2 = Article.objects.create(
            headline="First", pub_date=datetime(2005, 7, 30, 0, 0)
        )
        a3 = Article.objects.create(
            headline="First", pub_date=datetime(2005, 7, 30, 0, 0)
        )
        self.assertNotEqual(a3.id, a1.id)
        self.assertNotEqual(a3.id, a2.id)
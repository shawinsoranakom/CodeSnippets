def test_not_equal_and_equal_operators_behave_as_expected_on_instances(self):
        some_pub_date = datetime(2014, 5, 16, 12, 1)
        a1 = Article.objects.create(headline="First", pub_date=some_pub_date)
        a2 = Article.objects.create(headline="Second", pub_date=some_pub_date)
        self.assertNotEqual(a1, a2)
        self.assertEqual(a1, Article.objects.get(id__exact=a1.id))

        self.assertNotEqual(
            Article.objects.get(id__exact=a1.id), Article.objects.get(id__exact=a2.id)
        )
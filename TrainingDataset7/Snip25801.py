def test_values_filter_and_single_field(self):
        self.assertSequenceEqual(
            Article.objects.filter(pub_date__exact=datetime(2005, 7, 27)).values("id"),
            [{"id": self.a2.id}, {"id": self.a3.id}, {"id": self.a7.id}],
        )
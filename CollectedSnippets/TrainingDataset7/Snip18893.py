def test_leaving_off_a_field_with_default_set_the_default_will_be_saved(self):
        a = Article(pub_date=datetime(2005, 7, 31))
        a.save()
        self.assertEqual(a.headline, "Default headline")
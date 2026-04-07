def test_can_leave_off_value_for_autofield_and_it_gets_value_on_save(self):
        """
        You can leave off the value for an AutoField when creating an
        object, because it'll get filled in automatically when you save().
        """
        a = Article(headline="Article 5", pub_date=datetime(2005, 7, 31))
        a.save()
        self.assertEqual(a.headline, "Article 5")
        self.assertIsNotNone(a.id)
def test_positional_and_keyword_args_for_the_same_field(self):
        msg = "Article() got both positional and keyword arguments for field '%s'."
        with self.assertRaisesMessage(TypeError, msg % "headline"):
            Article(None, "Fifth article", headline="Other headline.")
        with self.assertRaisesMessage(TypeError, msg % "headline"):
            Article(None, "Sixth article", headline="")
        with self.assertRaisesMessage(TypeError, msg % "pub_date"):
            Article(None, "Seventh article", datetime(2021, 3, 1), pub_date=None)
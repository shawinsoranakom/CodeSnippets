def test_get_next_previous_by(self):
        # Every DateField and DateTimeField creates get_next_by_FOO() and
        # get_previous_by_FOO() methods. In the case of identical date values,
        # these methods will use the ID as a fallback check. This guarantees
        # that no records are skipped or duplicated.
        self.assertEqual(repr(self.a1.get_next_by_pub_date()), "<Article: Article 2>")
        self.assertEqual(repr(self.a2.get_next_by_pub_date()), "<Article: Article 3>")
        self.assertEqual(
            repr(self.a2.get_next_by_pub_date(headline__endswith="6")),
            "<Article: Article 6>",
        )
        self.assertEqual(repr(self.a3.get_next_by_pub_date()), "<Article: Article 7>")
        self.assertEqual(repr(self.a4.get_next_by_pub_date()), "<Article: Article 6>")
        with self.assertRaises(Article.DoesNotExist):
            self.a5.get_next_by_pub_date()
        self.assertEqual(repr(self.a6.get_next_by_pub_date()), "<Article: Article 5>")
        self.assertEqual(repr(self.a7.get_next_by_pub_date()), "<Article: Article 4>")

        self.assertEqual(
            repr(self.a7.get_previous_by_pub_date()), "<Article: Article 3>"
        )
        self.assertEqual(
            repr(self.a6.get_previous_by_pub_date()), "<Article: Article 4>"
        )
        self.assertEqual(
            repr(self.a5.get_previous_by_pub_date()), "<Article: Article 6>"
        )
        self.assertEqual(
            repr(self.a4.get_previous_by_pub_date()), "<Article: Article 7>"
        )
        self.assertEqual(
            repr(self.a3.get_previous_by_pub_date()), "<Article: Article 2>"
        )
        self.assertEqual(
            repr(self.a2.get_previous_by_pub_date()), "<Article: Article 1>"
        )
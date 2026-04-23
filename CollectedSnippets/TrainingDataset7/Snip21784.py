def test_full_clean(self):
        obj = DBArticle()
        obj.full_clean()
        obj.save()
        obj.refresh_from_db()
        self.assertEqual(obj.headline, "Default headline")

        obj = DBArticle(headline="Other title")
        obj.full_clean()
        obj.save()
        obj.refresh_from_db()
        self.assertEqual(obj.headline, "Other title")

        obj = DBArticle(headline="")
        with self.assertRaises(ValidationError):
            obj.full_clean()
def test_foreign_object_form(self):
        # A very crude test checking that the non-concrete fields do not get
        # form fields.
        form = FormsTests.ArticleForm()
        self.assertIn("id_pub_date", form.as_table())
        self.assertNotIn("active_translation", form.as_table())
        form = FormsTests.ArticleForm(data={"pub_date": str(datetime.date.today())})
        self.assertTrue(form.is_valid())
        a = form.save()
        self.assertEqual(a.pub_date, datetime.date.today())
        form = FormsTests.ArticleForm(instance=a, data={"pub_date": "2013-01-01"})
        a2 = form.save()
        self.assertEqual(a.pk, a2.pk)
        self.assertEqual(a2.pub_date, datetime.date(2013, 1, 1))
def test_year_view_allow_future(self):
        # Create a new book in the future
        year = datetime.date.today().year + 1
        Book.objects.create(
            name="The New New Testement", pages=600, pubdate=datetime.date(year, 1, 1)
        )
        res = self.client.get("/dates/books/%s/" % year)
        self.assertEqual(res.status_code, 404)

        res = self.client.get("/dates/books/%s/allow_empty/" % year)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(list(res.context["book_list"]), [])

        res = self.client.get("/dates/books/%s/allow_future/" % year)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(list(res.context["date_list"]), [datetime.date(year, 1, 1)])
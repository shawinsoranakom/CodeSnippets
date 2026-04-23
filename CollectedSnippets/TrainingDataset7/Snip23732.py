def test_week_view_allow_empty(self):
        # allow_empty = False, empty week
        res = self.client.get("/dates/books/2008/week/12/")
        self.assertEqual(res.status_code, 404)

        # allow_empty = True, empty month
        res = self.client.get("/dates/books/2008/week/12/allow_empty/")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(list(res.context["book_list"]), [])
        self.assertEqual(res.context["week"], datetime.date(2008, 3, 23))

        # Since allow_empty=True, next/prev are allowed to be empty weeks
        self.assertEqual(res.context["next_week"], datetime.date(2008, 3, 30))
        self.assertEqual(res.context["previous_week"], datetime.date(2008, 3, 16))

        # allow_empty but not allow_future: next_week should be empty
        url = (
            datetime.date.today()
            .strftime("/dates/books/%Y/week/%U/allow_empty/")
            .lower()
        )
        res = self.client.get(url)
        self.assertEqual(res.status_code, 200)
        self.assertIsNone(res.context["next_week"])
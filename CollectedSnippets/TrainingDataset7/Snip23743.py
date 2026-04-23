def test_day_view_allow_empty(self):
        # allow_empty = False, empty month
        res = self.client.get("/dates/books/2000/jan/1/")
        self.assertEqual(res.status_code, 404)

        # allow_empty = True, empty month
        res = self.client.get("/dates/books/2000/jan/1/allow_empty/")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(list(res.context["book_list"]), [])
        self.assertEqual(res.context["day"], datetime.date(2000, 1, 1))

        # Since it's allow empty, next/prev are allowed to be empty months
        # (#7164)
        self.assertEqual(res.context["next_day"], datetime.date(2000, 1, 2))
        self.assertEqual(res.context["previous_day"], datetime.date(1999, 12, 31))

        # allow_empty but not allow_future: next_month should be empty (#7164)
        url = (
            datetime.date.today().strftime("/dates/books/%Y/%b/%d/allow_empty/").lower()
        )
        res = self.client.get(url)
        self.assertEqual(res.status_code, 200)
        self.assertIsNone(res.context["next_day"])
def test_week_view_allow_future(self):
        # January 7th always falls in week 1, given Python's definition of week
        # numbers
        future = datetime.date(datetime.date.today().year + 1, 1, 7)
        future_sunday = future - datetime.timedelta(days=(future.weekday() + 1) % 7)
        b = Book.objects.create(name="The New New Testement", pages=600, pubdate=future)

        res = self.client.get("/dates/books/%s/week/1/" % future.year)
        self.assertEqual(res.status_code, 404)

        res = self.client.get("/dates/books/%s/week/1/allow_future/" % future.year)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(list(res.context["book_list"]), [b])
        self.assertEqual(res.context["week"], future_sunday)

        # Since allow_future = True but not allow_empty, next/prev are not
        # allowed to be empty weeks
        self.assertIsNone(res.context["next_week"])
        self.assertEqual(res.context["previous_week"], datetime.date(2008, 9, 28))

        # allow_future, but not allow_empty, with a current week. So next
        # should be in the future
        res = self.client.get("/dates/books/2008/week/39/allow_future/")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.context["next_week"], future_sunday)
        self.assertEqual(res.context["previous_week"], datetime.date(2006, 4, 30))
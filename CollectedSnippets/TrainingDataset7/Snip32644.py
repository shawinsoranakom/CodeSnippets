def test_feed_last_modified_time_naive_date(self):
        """
        Tests the Last-Modified header with naive publication dates.
        """
        response = self.client.get("/syndication/naive-dates/")
        self.assertEqual(
            response.headers["Last-Modified"], "Tue, 26 Mar 2013 01:00:00 GMT"
        )
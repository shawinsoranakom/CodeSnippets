def test_feed_last_modified_time(self):
        """
        Tests the Last-Modified header with aware publication dates.
        """
        response = self.client.get("/syndication/aware-dates/")
        self.assertEqual(
            response.headers["Last-Modified"], "Mon, 25 Mar 2013 19:18:00 GMT"
        )

        # No last-modified when feed has no item_pubdate
        response = self.client.get("/syndication/no_pubdate/")
        self.assertFalse(response.has_header("Last-Modified"))
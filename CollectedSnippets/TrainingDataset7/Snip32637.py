def test_aware_datetime_conversion(self):
        """
        Datetimes with timezones don't get trodden on.
        """
        response = self.client.get("/syndication/aware-dates/")
        doc = minidom.parseString(response.content)
        published = doc.getElementsByTagName("published")[0].firstChild.wholeText
        self.assertEqual(published[-6:], "+00:42")
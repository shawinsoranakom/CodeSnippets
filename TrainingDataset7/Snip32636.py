def test_naive_datetime_conversion(self):
        """
        Datetimes are correctly converted to the local time zone.
        """
        # Naive date times passed in get converted to the local time zone, so
        # check the received zone offset against the local offset.
        response = self.client.get("/syndication/naive-dates/")
        doc = minidom.parseString(response.content)
        updated = doc.getElementsByTagName("updated")[0].firstChild.wholeText

        d = Entry.objects.latest("published").published
        latest = rfc3339_date(timezone.make_aware(d, TZ))

        self.assertEqual(updated, latest)
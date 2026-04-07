def test_latest_post_date(self):
        """
        Both the published and updated dates are
        considered when determining the latest post date.
        """
        # this feed has a `published` element with the latest date
        response = self.client.get("/syndication/atom/")
        feed = minidom.parseString(response.content).firstChild
        updated = feed.getElementsByTagName("updated")[0].firstChild.wholeText

        d = Entry.objects.latest("published").published
        latest_published = rfc3339_date(timezone.make_aware(d, TZ))

        self.assertEqual(updated, latest_published)

        # this feed has an `updated` element with the latest date
        response = self.client.get("/syndication/latest/")
        feed = minidom.parseString(response.content).firstChild
        updated = feed.getElementsByTagName("updated")[0].firstChild.wholeText

        d = Entry.objects.exclude(title="My last entry").latest("updated").updated
        latest_updated = rfc3339_date(timezone.make_aware(d, TZ))

        self.assertEqual(updated, latest_updated)
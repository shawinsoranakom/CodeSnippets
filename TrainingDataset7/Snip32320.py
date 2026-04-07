def setUpTestData(cls):
        # Delete the site created as part of the default migration process.
        Site.objects.all().delete()
def test_manager_class_caching(self):
        e1 = Entry.objects.create()
        e2 = Entry.objects.create()
        t1 = Tag.objects.create()
        t2 = Tag.objects.create()

        # Get same manager twice in a row:
        self.assertIs(t1.entry_set.__class__, t1.entry_set.__class__)
        self.assertIs(e1.topics.__class__, e1.topics.__class__)

        # Get same manager for different instances
        self.assertIs(e1.topics.__class__, e2.topics.__class__)
        self.assertIs(t1.entry_set.__class__, t2.entry_set.__class__)
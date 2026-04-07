def test_overridable_test_loader(self):
        self.assertEqual(DiscoverRunner().test_loader, defaultTestLoader)
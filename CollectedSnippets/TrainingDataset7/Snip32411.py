def test_searched_locations(self):
        finders.find("spam")
        self.assertEqual(
            finders.searched_locations,
            [os.path.join(TEST_ROOT, "project", "documents")],
        )
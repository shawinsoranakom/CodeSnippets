def test_strip_tags_files(self):
        # Test with more lengthy content (also catching performance
        # regressions)
        for filename in ("strip_tags1.html", "strip_tags2.txt"):
            with self.subTest(filename=filename):
                path = os.path.join(os.path.dirname(__file__), "files", filename)
                with open(path) as fp:
                    content = fp.read()
                    start = datetime.now()
                    stripped = strip_tags(content)
                    elapsed = datetime.now() - start
                self.assertEqual(elapsed.seconds, 0)
                self.assertIn("Test string that has not been stripped.", stripped)
                self.assertNotIn("<", stripped)
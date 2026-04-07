def test_no_file(self):
        orig_file = django.__file__
        try:
            # Depending on the cwd, Python might give a local checkout
            # precedence over installed Django, producing None.
            django.__file__ = None
            self.assertEqual(django_file_prefixes(), ())
            del django.__file__
            self.assertEqual(django_file_prefixes(), ())
        finally:
            django.__file__ = orig_file
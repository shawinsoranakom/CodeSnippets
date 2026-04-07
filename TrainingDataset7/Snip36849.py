def test_development_no_file(self):
        get_git_changeset.cache_clear()
        version_file = django.utils.version.__file__
        try:
            del django.utils.version.__file__
            self.test_development()
        finally:
            django.utils.version.__file__ = version_file
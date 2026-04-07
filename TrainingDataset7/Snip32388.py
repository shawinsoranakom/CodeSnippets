def test_check_finders(self):
        """check_finders() concatenates all errors."""
        error1 = Error("1")
        error2 = Error("2")
        error3 = Error("3")

        def get_finders():
            class Finder1(BaseFinder):
                def check(self, **kwargs):
                    return [error1]

            class Finder2(BaseFinder):
                def check(self, **kwargs):
                    return []

            class Finder3(BaseFinder):
                def check(self, **kwargs):
                    return [error2, error3]

            class Finder4(BaseFinder):
                pass

            return [Finder1(), Finder2(), Finder3(), Finder4()]

        with mock.patch("django.contrib.staticfiles.checks.get_finders", get_finders):
            errors = check_finders(None)
            self.assertEqual(errors, [error1, error2, error3])
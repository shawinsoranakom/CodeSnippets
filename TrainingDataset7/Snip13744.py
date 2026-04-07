def check_subtest_picklable(self, test, subtest):
        try:
            self._confirm_picklable(subtest)
        except Exception as exc:
            self._print_unpicklable_subtest(test, subtest, exc)
            raise
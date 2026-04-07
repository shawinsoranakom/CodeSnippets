def assert_no_queries(test):
    @wraps(test)
    def inner(self):
        with self.assertNumQueries(0):
            test(self)

    return inner
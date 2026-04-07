def test_unicode_chars_in_queries(self):
        """
        Regression tests for #3937

        make sure we can use unicode characters in queries.
        If these tests fail on MySQL, it's a problem with the test setup.
        A properly configured UTF-8 database can handle this.
        """

        fx = Foo(name="Bjorn", friend="François")
        fx.save()
        self.assertEqual(Foo.objects.get(friend__contains="\xe7"), fx)
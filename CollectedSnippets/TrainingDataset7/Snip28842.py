def test_unsupported_unpickle(self):
        """
        #21430 -- Verifies a warning is raised for models that are
        unpickled with a different Django version than the current
        """

        class DifferentDjangoVersion(models.Model):
            title = models.CharField(max_length=10)

            def __reduce__(self):
                reduce_list = super().__reduce__()
                data = reduce_list[-1]
                data[DJANGO_VERSION_PICKLE_KEY] = "1.0"
                return reduce_list

        p = DifferentDjangoVersion(title="FooBar")
        msg = (
            "Pickled model instance's Django version 1.0 does not match the "
            "current version %s." % django.__version__
        )
        with self.assertRaisesMessage(RuntimeWarning, msg):
            pickle.loads(pickle.dumps(p))
def wrapper(mutation_func):
        def test(test_case_instance, *args, **kwargs):
            class TestFunc(models.Func):
                output_field = models.IntegerField()

                def __init__(self):
                    self.attribute = "initial"
                    super().__init__("initial", ["initial"])

                def as_sql(self, *args, **kwargs):
                    mutation_func(self)
                    return "", ()

            if raises:
                msg = "TestFunc Func was mutated during compilation."
                with test_case_instance.assertRaisesMessage(AssertionError, msg):
                    getattr(TestFunc(), "as_" + connection.vendor)(None, None)
            else:
                getattr(TestFunc(), "as_" + connection.vendor)(None, None)

        return test
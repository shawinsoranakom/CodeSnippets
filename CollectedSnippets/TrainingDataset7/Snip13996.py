def __init__(self, *args, **kwargs):
        if args:
            # Hack used when instantiating from SimpleTestCase.setUpClass.
            assert not kwargs
            self.operations = args[0]
        else:
            assert not args
            self.operations = list(kwargs.items())
        super(override_settings, self).__init__()
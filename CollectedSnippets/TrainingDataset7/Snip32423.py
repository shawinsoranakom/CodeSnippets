def raises_exception(cls):
        try:
            super().setUpClass()
        except ImproperlyConfigured:
            # This raises ImproperlyConfigured("You're using the staticfiles
            # app without having set the required STATIC_URL setting.")
            pass
        else:
            raise Exception("setUpClass() should have raised an exception.")
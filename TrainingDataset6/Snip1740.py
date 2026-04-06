def fail_on_warning(self):
        warnings.simplefilter('error')
        yield
        warnings.resetwarnings()
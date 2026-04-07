def ipython(self, options):
        from IPython import start_ipython

        start_ipython(argv=[], user_ns=self.get_namespace(**options))
def bpython(self, options):
        import bpython

        bpython.embed(self.get_namespace(**options))
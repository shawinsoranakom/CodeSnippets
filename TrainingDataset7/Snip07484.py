def _set_argtypes(self, argtypes):
        self.cfunc.argtypes = [CONTEXT_PTR, *argtypes]
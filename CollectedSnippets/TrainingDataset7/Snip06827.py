def __init__(self, lhs, rhs):
        rhs, *self.rhs_params = rhs if isinstance(rhs, (list, tuple)) else (rhs,)
        super().__init__(lhs, rhs)
        self.template_params = {}
        self.process_rhs_params()
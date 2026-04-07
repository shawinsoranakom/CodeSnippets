def add_filter(self, filter_lhs, filter_rhs):
        self.add_q(Q((filter_lhs, filter_rhs)))
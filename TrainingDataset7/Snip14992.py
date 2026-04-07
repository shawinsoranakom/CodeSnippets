def visit_console_dummy(self, node):
    """Defer to the corresponding parent's handler."""
    self.visit_literal_block(node)
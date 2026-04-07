def __copy__(self):
        duplicate = super().__copy__()
        duplicate.render_context = copy(self.render_context)
        return duplicate
def format_position(self, position=None, element=None):
        if not position and element:
            position = self.element_positions[element]
        if position is None:
            position = self.getpos()
        if hasattr(position, "lineno"):
            position = position.lineno, position.offset
        return "Line %d, Column %d" % position
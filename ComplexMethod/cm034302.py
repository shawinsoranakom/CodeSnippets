def __str__(self) -> str:
        """Renders the origin in the form of path:line_num:col_num, omitting missing/invalid elements from the right."""
        if self.path:
            value = self.path
        else:
            value = self.description

        if self.line_num and self.line_num > 0:
            value += f':{self.line_num}'

            if self.col_num and self.col_num > 0:
                value += f':{self.col_num}'

        if self.path and self.description:
            value += f' ({self.description})'

        return value
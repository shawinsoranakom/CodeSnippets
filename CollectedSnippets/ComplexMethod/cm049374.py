def stringify(self, annotation=True, default=True, return_annotation=True):
        out = ['(']
        for name, param in self.parameters.items():
            out.append(name)
            if annotation and param.annotation:
                out.append(f': {param.annotation}')
                if default and param.default is not inspect._empty:
                    out.append(f' = {param.default!r}')
            elif default and param.default is not inspect._empty:
                out.append(f'={param.default!r}')
            out.append(', ')
        if self.parameters:
            out.pop()  # remove trailing ', '
        out.append(')')
        if return_annotation and self.return_.annotation:
            out.append(f' -> {self.return_.annotation}')
        return ''.join(out)
def __str__(self):
        info = [self.error]
        if self.template is not None:
            info.append(f'Template: {self.template}')
        if self.ref is not None:
            info.append(f'Reference: {self.ref}')
        if self.path is not None:
            info.append(f'Path: {self.path}')
        if self.element is not None:
            info.append(f'Element: {self.element}')
        if self.source:
            source = '\n          '.join(str(v) for v in self.source)
            info.append(f'From: {source}')
        if self.surrounding:
            info.append(f'QWeb generated code:\n{self.surrounding}')
        return '\n    '.join(info)
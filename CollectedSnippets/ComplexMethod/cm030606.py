def resolve_interp(self, interp, other, extra):
        if self.interp == 'same':
            return interp
        elif self.interp == 'other':
            if other is None:
                raise RuntimeError
            return other
        elif self.interp == 'extra':
            if extra is None:
                raise RuntimeError
            return extra
        elif self.interp == 'main':
            if interp.name == 'main':
                return interp
            elif other and other.name == 'main':
                return other
            else:
                raise RuntimeError
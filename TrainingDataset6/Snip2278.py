def and_(self, *commands):
        return u' -and '.join('({0})'.format(c) for c in commands)
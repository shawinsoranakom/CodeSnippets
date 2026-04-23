def render(self, fmt='line', *, itemonly=False):
        if fmt == 'raw':
            yield repr(self)
            return
        rendered = super().render(fmt, itemonly=itemonly)
        # XXX ???
        #if itemonly:
        #    yield from rendered
        supported = self.supported
        if fmt in ('line', 'brief'):
            rendered, = rendered
            parts = [
                '+' if supported else '-' if supported is False else '',
                rendered,
            ]
            yield '\t'.join(parts)
        elif fmt == 'summary':
            raise NotImplementedError(fmt)
        elif fmt == 'full':
            yield from rendered
            if supported:
                yield f'\tsupported:\t{supported}'
        else:
            raise NotImplementedError(fmt)
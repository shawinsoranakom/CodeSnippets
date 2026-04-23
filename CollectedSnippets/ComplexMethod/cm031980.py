def render(self, fmt='line', *, itemonly=False):
        if fmt == 'raw':
            yield repr(self)
            return
        rendered = self.item.render(fmt)
        if itemonly or not self._extra:
            yield from rendered
            return
        extra = self._render_extra(fmt)
        if not extra:
            yield from rendered
        elif fmt in ('brief', 'line'):
            rendered, = rendered
            extra, = extra
            yield f'{rendered}\t{extra}'
        elif fmt == 'summary':
            raise NotImplementedError(fmt)
        elif fmt == 'full':
            yield from rendered
            for line in extra:
                yield f'\t{line}'
        else:
            raise NotImplementedError(fmt)
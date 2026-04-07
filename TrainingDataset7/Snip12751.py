def render_css(self):
        # To keep rendering order consistent, we can't just iterate over
        # items(). We need to sort the keys, and iterate over the sorted list.
        media = sorted(self._css)
        return chain.from_iterable(
            [
                (
                    path.__html__()
                    if hasattr(path, "__html__")
                    else format_html(
                        '<link href="{}" media="{}" rel="stylesheet">',
                        self.absolute_path(path),
                        medium,
                    )
                )
                for path in self._css[medium]
            ]
            for medium in media
        )
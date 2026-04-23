def render(self):
        return mark_safe(
            "\n".join(
                chain.from_iterable(
                    getattr(self, "render_" + name)() for name in MEDIA_TYPES
                )
            )
        )
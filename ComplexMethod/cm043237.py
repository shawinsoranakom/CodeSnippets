def _resolve_source(self, element, source: str):
        source = source.strip()
        if not source.startswith("+"):
            return None
        sel = source[1:].strip()  # e.g. "tr", "tr.subtext", ".classname"
        parts = sel.split(".")
        tag = parts[0].strip() or None
        classes = [p.strip() for p in parts[1:] if p.strip()]
        kwargs = {}
        if classes:
            kwargs["class_"] = lambda c, _cls=classes: c and all(
                cl in c for cl in _cls
            )
        return element.find_next_sibling(tag, **kwargs)
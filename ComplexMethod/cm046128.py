def highlight_labels(nodes):
        """Inject doc-kind badges into headings and nav entries."""
        nonlocal modified

        for node in nodes:
            if not node.contents:
                continue
            first = node.contents[0]
            if hasattr(first, "get") and "doc-kind" in (first.get("class") or []):
                continue
            text = first if isinstance(first, str) else getattr(first, "string", "")
            if not text:
                continue
            stripped = str(text).strip()
            if not stripped:
                continue
            kind = stripped.split()[0].rstrip(":")
            if kind not in DOC_KIND_LABELS:
                continue
            span = soup.new_tag("span", attrs={"class": f"doc-kind doc-kind-{kind.lower()}"})
            span.string = kind.lower()
            first.replace_with(span)
            tail = str(text)[len(kind) :]
            tail_stripped = tail.lstrip()
            if tail_stripped.startswith(kind):
                tail = tail_stripped[len(kind) :]
            if not tail and len(node.contents) > 0:
                tail = " "
            if tail:
                span.insert_after(tail)
            modified = True
def walk_files(path, allowed_extensions=None):
    if not os.path.exists(path):
        return

    if allowed_extensions is not None:
        allowed_extensions = set(allowed_extensions)

    items = list(os.walk(path, followlinks=True))
    items = sorted(items, key=lambda x: natural_sort_key(x[0]))

    for root, _, files in items:
        for filename in sorted(files, key=natural_sort_key):
            if allowed_extensions is not None:
                _, ext = os.path.splitext(filename)
                if ext.lower() not in allowed_extensions:
                    continue

            if not shared.opts.list_hidden_files and ("/." in root or "\\." in root):
                continue

            yield os.path.join(root, filename)
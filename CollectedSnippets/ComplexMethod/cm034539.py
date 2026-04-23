def _iter_modules_impl(paths, prefix=''):
    # NB: this currently only iterates what's on disk- redirected modules are not considered
    if not prefix:
        prefix = ''
    else:
        prefix = _to_text(prefix)
    # yield (module_loader, name, ispkg) for each module/pkg under path
    # TODO: implement ignore/silent catch for unreadable?
    for b_path in map(_to_bytes, paths):
        if not os.path.isdir(b_path):
            continue
        for b_basename in sorted(os.listdir(b_path)):
            b_candidate_module_path = os.path.join(b_path, b_basename)
            if os.path.isdir(b_candidate_module_path):
                # exclude things that obviously aren't Python package dirs
                # FIXME: this dir is adjustable in py3.8+, check for it
                if b'.' in b_basename or b_basename == b'__pycache__':
                    continue

                # TODO: proper string handling?
                yield prefix + _to_text(b_basename), True
            else:
                # FIXME: match builtin ordering for package/dir/file, support compiled?
                if b_basename.endswith(b'.py') and b_basename != b'__init__.py':
                    yield prefix + _to_text(os.path.splitext(b_basename)[0]), False
def find_existing_collections(path_filter, artifacts_manager, namespace_filter=None, collection_filter=None, dedupe=True):
    """Locate all collections under a given path.

    :param path: Collection dirs layout search path.
    :param artifacts_manager: Artifacts manager.
    """
    if path_filter and not is_sequence(path_filter):
        path_filter = [path_filter]
    if namespace_filter and not is_sequence(namespace_filter):
        namespace_filter = [namespace_filter]
    if collection_filter and not is_sequence(collection_filter):
        collection_filter = [collection_filter]

    paths = set()
    for path in files('ansible_collections').glob('*/*/'):
        path = _normalize_collection_path(path)
        if not path.is_dir():
            continue
        if path_filter:
            for pf in path_filter:
                try:
                    path.relative_to(_normalize_collection_path(pf))
                except ValueError:
                    continue
                break
            else:
                continue
        paths.add(path)

    seen = set()
    for path in paths:
        namespace = path.parent.name
        name = path.name
        if namespace_filter and namespace not in namespace_filter:
            continue
        if collection_filter and name not in collection_filter:
            continue

        if dedupe:
            try:
                collection_path = files(f'ansible_collections.{namespace}.{name}')
            except ImportError:
                continue
            if collection_path in seen:
                continue
            seen.add(collection_path)
        else:
            collection_path = path

        b_collection_path = to_bytes(collection_path.as_posix())

        try:
            req = Candidate.from_dir_path_as_unknown(b_collection_path, artifacts_manager)
        except ValueError as val_err:
            display.warning(f'{val_err}')
            continue

        if req.fqcn != '.'.join(pathlib.Path(to_text(req.src)).parts[-2:]):
            display.warning(f"Collection at {to_text(req.src)} documents incorrect FQCN '{req.fqcn}'. Ignoring metadata.")
            req = Candidate.from_dir_path_implicit(b_collection_path)

        display.vvv(
            u"Found installed collection {coll!s} at '{path!s}'".
            format(coll=to_text(req), path=to_text(req.src))
        )
        yield req
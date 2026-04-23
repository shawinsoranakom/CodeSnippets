def execute_list_collection(self, artifacts_manager=None):
        """
        List all collections installed on the local system

        :param artifacts_manager: Artifacts manager.
        """
        if artifacts_manager is not None:
            artifacts_manager.require_build_metadata = False

        output_format = context.CLIARGS['output_format']
        collection_name = context.CLIARGS['collection']
        default_collections_path = set(C.COLLECTIONS_PATHS)
        collections_search_paths = (
            set(context.CLIARGS['collections_path'] or []) | default_collections_path | set(self.collection_paths)
        )
        collections_in_paths = {}

        warnings = []
        path_found = False
        collection_found = False

        namespace_filter = None
        collection_filter = None
        if collection_name:
            # list a specific collection

            validate_collection_name(collection_name)
            namespace_filter, collection_filter = collection_name.split('.')

        collections = list(find_existing_collections(
            list(collections_search_paths),
            artifacts_manager,
            namespace_filter=namespace_filter,
            collection_filter=collection_filter,
            dedupe=False
        ))

        seen = set()
        fqcn_width, version_width = _get_collection_widths(collections)
        for collection in sorted(collections, key=lambda c: c.src):
            collection_found = True
            collection_path = pathlib.Path(to_text(collection.src)).parent.parent.as_posix()

            if output_format in {'yaml', 'json'}:
                collections_in_paths.setdefault(collection_path, {})
                collections_in_paths[collection_path][collection.fqcn] = {'version': collection.ver}
            else:
                if collection_path not in seen:
                    _display_header(
                        collection_path,
                        'Collection',
                        'Version',
                        fqcn_width,
                        version_width
                    )
                    seen.add(collection_path)
                _display_collection(collection, fqcn_width, version_width)

        path_found = False
        for path in collections_search_paths:
            if not os.path.exists(path):
                if path in default_collections_path:
                    # don't warn for missing default paths
                    continue
                warnings.append("- the configured path {0} does not exist.".format(path))
            elif os.path.exists(path) and not os.path.isdir(path):
                warnings.append("- the configured path {0}, exists, but it is not a directory.".format(path))
            else:
                path_found = True

        # Do not warn if the specific collection was found in any of the search paths
        if collection_found and collection_name:
            warnings = []

        for w in warnings:
            display.warning(w)

        if not collections and not path_found:
            display.warning(
                "None of the provided paths were usable. Please specify a valid path with --{0}s-path.".format(context.CLIARGS['type'])
            )

        if output_format == 'json':
            display.display(json.dumps(collections_in_paths))
        elif output_format == 'yaml':
            display.display(yaml_dump(collections_in_paths))

        return 0
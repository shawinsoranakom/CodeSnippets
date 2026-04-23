def get_direct_collection_meta(self, collection):
        # type: (Collection) -> dict[str, t.Union[str, dict[str, str], list[str], None, t.Type[Sentinel]]]
        """Extract meta from the given on-disk collection artifact."""
        try:  # FIXME: use unique collection identifier as a cache key?
            return self._artifact_meta_cache[collection.src]
        except KeyError:
            b_artifact_path = self.get_artifact_path(collection)

        if collection.is_url or collection.is_file:
            collection_meta = _get_meta_from_tar(b_artifact_path)
        elif collection.is_dir:  # should we just build a coll instead?
            # FIXME: what if there's subdirs?
            try:
                collection_meta = _get_meta_from_dir(b_artifact_path, self.require_build_metadata)
            except LookupError as lookup_err:
                raise AnsibleError(
                    'Failed to find the collection dir deps: {err!s}'.
                    format(err=to_native(lookup_err)),
                ) from lookup_err
        elif collection.is_scm:
            collection_meta = {
                'name': None,
                'namespace': None,
                'dependencies': {to_native(b_artifact_path): '*'},
                'version': '*',
            }
        elif collection.is_subdirs:
            collection_meta = {
                'name': None,
                'namespace': None,
                # NOTE: Dropping b_artifact_path since it's based on src anyway
                'dependencies': dict.fromkeys(
                    map(to_native, collection.namespace_collection_paths),
                    '*',
                ),
                'version': '*',
            }
        else:
            raise RuntimeError

        self._artifact_meta_cache[collection.src] = collection_meta
        return collection_meta
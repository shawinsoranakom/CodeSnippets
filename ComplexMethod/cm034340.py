def verify_collections(
        collections,  # type: t.Iterable[Requirement]
        search_paths,  # type: t.Iterable[str]
        apis,  # type: t.Iterable[GalaxyAPI]
        ignore_errors,  # type: bool
        local_verify_only,  # type: bool
        artifacts_manager,  # type: ConcreteArtifactsManager
):  # type: (...) -> list[CollectionVerifyResult]
    r"""Verify the integrity of locally installed collections.

    :param collections: The collections to check.
    :param search_paths: Locations for the local collection lookup.
    :param apis: A list of GalaxyAPIs to query when searching for a collection.
    :param ignore_errors: Whether to ignore any errors when verifying the collection.
    :param local_verify_only: When True, skip downloads and only verify local manifests.
    :param artifacts_manager: Artifacts manager.
    :return: list of CollectionVerifyResult objects describing the results of each collection verification
    """
    results = []  # type: list[CollectionVerifyResult]

    api_proxy = MultiGalaxyAPIProxy(apis, artifacts_manager)

    with _display_progress():
        for collection in collections:
            try:
                if collection.is_concrete_artifact:
                    raise AnsibleError(
                        message="'{coll_type!s}' type is not supported. "
                        'The format namespace.name is expected.'.
                        format(coll_type=collection.type)
                    )

                # NOTE: Verify local collection exists before
                # NOTE: downloading its source artifact from
                # NOTE: a galaxy server.
                default_err = 'Collection %s is not installed in any of the collection paths.' % collection.fqcn
                for search_path in search_paths:
                    b_search_path = to_bytes(
                        os.path.join(
                            search_path,
                            collection.namespace, collection.name,
                        ),
                        errors='surrogate_or_strict',
                    )
                    if not os.path.isdir(b_search_path):
                        continue
                    if not _is_installed_collection_dir(b_search_path):
                        default_err = (
                            "Collection %s does not have a MANIFEST.json. "
                            "A MANIFEST.json is expected if the collection has been built "
                            "and installed via ansible-galaxy" % collection.fqcn
                        )
                        continue

                    local_collection = Candidate.from_dir_path(
                        b_search_path, artifacts_manager,
                    )

                    if local_collection.fqcn != collection.fqcn:
                        default_err = f"Collection at '{to_text(local_collection.src)}' documents incorrect FQCN '{local_collection.fqcn}'"
                        continue

                    supplemental_signatures = [
                        get_signature_from_source(source, display)
                        for source in collection.signature_sources or []
                    ]
                    local_collection = Candidate(
                        local_collection.fqcn,
                        local_collection.ver,
                        local_collection.src,
                        local_collection.type,
                        signatures=frozenset(supplemental_signatures),
                    )

                    break
                else:
                    raise AnsibleError(message=default_err)

                if local_verify_only:
                    remote_collection = None
                else:
                    signatures = api_proxy.get_signatures(local_collection)
                    signatures.extend([
                        get_signature_from_source(source, display)
                        for source in collection.signature_sources or []
                    ])

                    remote_collection = Candidate(
                        collection.fqcn,
                        collection.ver if collection.ver != '*'
                        else local_collection.ver,
                        None, 'galaxy',
                        frozenset(signatures),
                    )

                    # Download collection on a galaxy server for comparison
                    try:
                        # NOTE: If there are no signatures, trigger the lookup. If found,
                        # NOTE: it'll cache download URL and token in artifact manager.
                        # NOTE: If there are no Galaxy server signatures, only user-provided signature URLs,
                        # NOTE: those alone validate the MANIFEST.json and the remote collection is not downloaded.
                        # NOTE: The remote MANIFEST.json is only used in verification if there are no signatures.
                        if artifacts_manager.keyring is None or not signatures:
                            api_proxy.get_collection_version_metadata(
                                remote_collection,
                            )
                    except AnsibleError as e:  # FIXME: does this actually emit any errors?
                        # FIXME: extract the actual message and adjust this:
                        expected_error_msg = (
                            'Failed to find collection {coll.fqcn!s}:{coll.ver!s}'.
                            format(coll=collection)
                        )
                        if e.message == expected_error_msg:
                            raise AnsibleError(
                                'Failed to find remote collection '
                                "'{coll!s}' on any of the galaxy servers".
                                format(coll=collection)
                            )
                        raise

                result = verify_local_collection(local_collection, remote_collection, artifacts_manager)

                results.append(result)

            except AnsibleError as err:
                if ignore_errors:
                    display.warning(
                        "Failed to verify collection '{coll!s}' but skipping "
                        'due to --ignore-errors being set. '
                        'Error: {err!s}'.
                        format(coll=collection, err=to_text(err)),
                    )
                else:
                    raise

    return results
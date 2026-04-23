def from_requirement_dict(
        cls,
        # NOTE: The actual `collection_req` shape is supposed to be
        # NOTE: `dict[str, str | list[str] | None]`
        collection_req: dict[str, t.Any],
        art_mgr: ConcreteArtifactsManager,
        validate_signature_options: bool = True,
    ) -> t.Self:
        req_name = collection_req.get('name', None)
        req_version = collection_req.get('version', '*')
        req_type = collection_req.get('type')
        # TODO: decide how to deprecate the old src API behavior
        req_source = collection_req.get('source', None)
        req_signature_sources = collection_req.get('signatures', None)
        if req_signature_sources is not None:
            if validate_signature_options and art_mgr.keyring is None:
                raise AnsibleError(
                    f"Signatures were provided to verify {req_name} but no keyring was configured."
                )

            if not isinstance(req_signature_sources, _c.MutableSequence):
                req_signature_sources = [req_signature_sources]
            req_signature_sources = frozenset(req_signature_sources)

        if req_type is None:
            if (  # FIXME: decide on the future behavior:
                    _ALLOW_CONCRETE_POINTER_IN_SOURCE
                    and req_source is not None
                    and _is_concrete_artifact_pointer(req_source)
            ):
                src_path = req_source
            elif (
                    req_name is not None
                    and AnsibleCollectionRef.is_valid_collection_name(req_name)
            ):
                req_type = 'galaxy'
            elif (
                    req_name is not None
                    and _is_concrete_artifact_pointer(req_name)
            ):
                src_path, req_name = req_name, None
            else:
                dir_tip_tmpl = (  # NOTE: leading LFs are for concat
                    '\n\nTip: Make sure you are pointing to the right '
                    'subdirectory — `{src!s}` looks like a directory '
                    'but it is neither a collection, nor a namespace '
                    'dir.'
                )

                if req_source is not None and os.path.isdir(req_source):
                    tip = dir_tip_tmpl.format(src=req_source)
                elif req_name is not None and os.path.isdir(req_name):
                    tip = dir_tip_tmpl.format(src=req_name)
                elif req_name:
                    tip = '\n\nCould not find {0}.'.format(req_name)
                else:
                    tip = ''

                raise AnsibleError(  # NOTE: I'd prefer a ValueError instead
                    'Neither the collection requirement entry key '
                    "'name', nor 'source' point to a concrete "
                    "resolvable collection artifact. Also 'name' is "
                    'not an FQCN. A valid collection name must be in '
                    'the format <namespace>.<collection>. Please make '
                    'sure that the namespace and the collection name '
                    'contain characters from [a-zA-Z0-9_] only.'
                    '{extra_tip!s}'.format(extra_tip=tip),
                )

        if req_type is None:
            if _is_git_url(src_path):
                req_type = 'git'
                req_source = src_path
            elif _is_http_url(src_path):
                req_type = 'url'
                req_source = src_path
            elif _is_file_path(src_path):
                req_type = 'file'
                req_source = src_path
            elif _is_collection_dir(src_path):
                if _is_installed_collection_dir(src_path) and _is_collection_src_dir(src_path):
                    # Note that ``download`` requires a dir with a ``galaxy.yml`` and fails if it
                    # doesn't exist, but if a ``MANIFEST.json`` also exists, it would be used
                    # instead of the ``galaxy.yml``.
                    raise AnsibleError(
                        u"Collection requirement at '{path!s}' has both a {manifest_json!s} "
                        u"file and a {galaxy_yml!s}.\nThe requirement must either be an installed "
                        u"collection directory or a source collection directory, not both.".
                        format(
                            path=to_text(src_path, errors='surrogate_or_strict'),
                            manifest_json=to_text(_MANIFEST_JSON),
                            galaxy_yml=to_text(_GALAXY_YAML),
                        )
                    )
                req_type = 'dir'
                req_source = src_path
            elif _is_collection_namespace_dir(src_path):
                req_name = None  # No name for a virtual req or "namespace."?
                req_type = 'subdirs'
                req_source = src_path
            else:
                raise AnsibleError(  # NOTE: this is never supposed to be hit
                    'Failed to automatically detect the collection '
                    'requirement type.',
                )

        if req_type not in {'file', 'galaxy', 'git', 'url', 'dir', 'subdirs'}:
            raise AnsibleError(
                "The collection requirement entry key 'type' must be "
                'one of file, galaxy, git, dir, subdirs, or url.'
            )

        if req_name is None and req_type == 'galaxy':
            raise AnsibleError(
                'Collections requirement entry should contain '
                "the key 'name' if it's requested from a Galaxy-like "
                'index server.',
            )

        if req_type != 'galaxy' and req_source is None:
            req_source, req_name = req_name, None

        if (
                req_type == 'galaxy' and
                isinstance(req_source, GalaxyAPI) and
                not _is_http_url(req_source.api_server)
        ):
            raise AnsibleError(
                "Collections requirement 'source' entry should contain "
                'a valid Galaxy API URL but it does not: {not_url!s} '
                'is not an HTTP URL.'.
                format(not_url=req_source.api_server),
            )

        if (
                req_type == 'dir'
                and isinstance(req_source, str)
                and req_source.endswith(os.path.sep)
        ):
            req_source = req_source.rstrip(os.path.sep)

        tmp_inst_req = cls(req_name, req_version, req_source, req_type, req_signature_sources)

        if req_type not in {'galaxy', 'subdirs'} and req_name is None:
            req_name = art_mgr.get_direct_collection_fqcn(tmp_inst_req)  # TODO: fix the cache key in artifacts manager?

        if req_type not in {'galaxy', 'subdirs'} and req_version == '*':
            req_version = art_mgr.get_direct_collection_version(tmp_inst_req)

        return cls(
            req_name, req_version,
            req_source, req_type,
            req_signature_sources,
        )
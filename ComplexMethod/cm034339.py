def install_collections(
        collections,  # type: t.Iterable[Requirement]
        output_path,  # type: str
        apis,  # type: t.Iterable[GalaxyAPI]
        ignore_errors,  # type: bool
        no_deps,  # type: bool
        force,  # type: bool
        force_deps,  # type: bool
        upgrade,  # type: bool
        allow_pre_release,  # type: bool
        artifacts_manager,  # type: ConcreteArtifactsManager
        disable_gpg_verify,  # type: bool
        offline,  # type: bool
        read_requirement_paths,  # type: set[str]
):  # type: (...) -> None
    """Install Ansible collections to the path specified.

    :param collections: The collections to install.
    :param output_path: The path to install the collections to.
    :param apis: A list of GalaxyAPIs to query when searching for a collection.
    :param validate_certs: Whether to validate the certificates if downloading a tarball.
    :param ignore_errors: Whether to ignore any errors when installing the collection.
    :param no_deps: Ignore any collection dependencies and only install the base requirements.
    :param force: Re-install a collection if it has already been installed.
    :param force_deps: Re-install a collection as well as its dependencies if they have already been installed.
    """
    existing_collections = {
        Requirement(coll.fqcn, coll.ver, coll.src, coll.type, None)
        for path in {output_path} | read_requirement_paths
        for coll in find_existing_collections(path, artifacts_manager)
    }

    unsatisfied_requirements = set(
        chain.from_iterable(
            (
                Requirement.from_dir_path(to_bytes(sub_coll), artifacts_manager)
                for sub_coll in (
                    artifacts_manager.
                    get_direct_collection_dependencies(install_req).
                    keys()
                )
            )
            if install_req.is_subdirs else (install_req, )
            for install_req in collections
        ),
    )
    requested_requirements_names = {req.fqcn for req in unsatisfied_requirements}

    # NOTE: Don't attempt to reevaluate already installed deps
    # NOTE: unless `--force` or `--force-with-deps` is passed
    unsatisfied_requirements -= set() if force or force_deps else {
        req
        for req in unsatisfied_requirements
        for exs in existing_collections
        if req.fqcn == exs.fqcn and meets_requirements(exs.ver, req.ver)
    }

    if not unsatisfied_requirements and not upgrade:
        display.display(
            'Nothing to do. All requested collections are already '
            'installed. If you want to reinstall them, '
            'consider using `--force`.'
        )
        return

    # FIXME: This probably needs to be improved to
    # FIXME: properly match differing src/type.
    existing_non_requested_collections = {
        coll for coll in existing_collections
        if coll.fqcn not in requested_requirements_names
    }

    preferred_requirements = (
        [] if force_deps
        else existing_non_requested_collections if force
        else existing_collections
    )
    preferred_collections = {
        # NOTE: No need to include signatures if the collection is already installed
        Candidate(coll.fqcn, coll.ver, coll.src, coll.type, None)
        for coll in preferred_requirements
    }
    with _display_progress("Process install dependency map"):
        dependency_map = _resolve_depenency_map(
            collections,
            galaxy_apis=apis,
            preferred_candidates=preferred_collections,
            concrete_artifacts_manager=artifacts_manager,
            no_deps=no_deps,
            allow_pre_release=allow_pre_release,
            upgrade=upgrade,
            include_signatures=not disable_gpg_verify,
            offline=offline,
        )

    keyring_exists = artifacts_manager.keyring is not None
    with _display_progress("Starting collection install process"):
        for fqcn, concrete_coll_pin in dependency_map.items():
            if concrete_coll_pin.type == "requires_ansible":
                continue
            if concrete_coll_pin.is_virtual:
                display.vvvv(
                    "Encountered {coll!s}, skipping.".
                    format(coll=to_text(concrete_coll_pin)),
                )
                continue

            if concrete_coll_pin in preferred_collections:
                display.display(
                    "'{coll!s}' is already installed, skipping.".
                    format(coll=to_text(concrete_coll_pin)),
                )
                continue

            if not disable_gpg_verify and concrete_coll_pin.signatures and not keyring_exists:
                # Duplicate warning msgs are not displayed
                display.warning(
                    "The GnuPG keyring used for collection signature "
                    "verification was not configured but signatures were "
                    "provided by the Galaxy server to verify authenticity. "
                    "Configure a keyring for ansible-galaxy to use "
                    "or disable signature verification. "
                    "Skipping signature verification."
                )

            if concrete_coll_pin.type == 'galaxy':
                concrete_coll_pin = concrete_coll_pin.with_signatures_repopulated()

            try:
                install(concrete_coll_pin, output_path, artifacts_manager)
            except AnsibleError as err:
                if ignore_errors:
                    display.warning(
                        'Failed to install collection {coll!s} but skipping '
                        'due to --ignore-errors being set. Error: {error!s}'.
                        format(
                            coll=to_text(concrete_coll_pin),
                            error=to_text(err),
                        )
                    )
                else:
                    raise
def _resolve_depenency_map(
        requested_requirements,  # type: t.Iterable[Requirement]
        galaxy_apis,  # type: t.Iterable[GalaxyAPI]
        concrete_artifacts_manager,  # type: ConcreteArtifactsManager
        preferred_candidates,  # type: t.Iterable[Candidate] | None
        no_deps,  # type: bool
        allow_pre_release,  # type: bool
        upgrade,  # type: bool
        include_signatures,  # type: bool
        offline,  # type: bool
):  # type: (...) -> dict[str, Candidate]
    """Return the resolved dependency map."""
    if not HAS_RESOLVELIB:
        raise AnsibleError("Failed to import resolvelib, check that a supported version is installed")
    if not HAS_PACKAGING:
        raise AnsibleError("Failed to import packaging, check that a supported version is installed")

    req = None

    try:
        dist = distribution('ansible-core')
    except Exception:
        pass
    else:
        req = next((rr for r in (dist.requires or []) if (rr := PkgReq(r)).name == 'resolvelib'), None)
    finally:
        if req is None:
            # TODO: replace the hardcoded versions with a warning if the dist info is missing
            # display.warning("Unable to find 'ansible-core' distribution requirements to verify the resolvelib version is supported.")
            if not RESOLVELIB_LOWERBOUND <= RESOLVELIB_VERSION < RESOLVELIB_UPPERBOUND:
                raise AnsibleError(
                    f"ansible-galaxy requires resolvelib<{RESOLVELIB_UPPERBOUND.vstring},>={RESOLVELIB_LOWERBOUND.vstring}"
                )
        elif not req.specifier.contains(RESOLVELIB_VERSION.vstring):
            raise AnsibleError(f"ansible-galaxy requires {req.name}{req.specifier}")

    pre_release_hint = '' if allow_pre_release else (
        'Hint: Pre-releases hosted on Galaxy or Automation Hub are not '
        'installed by default unless a specific version is requested. '
        'To enable pre-releases globally, use --pre.'
    )
    requires_ansible_hint = '' if C.COLLECTIONS_ON_ANSIBLE_VERSION_MISMATCH == 'ignore' else (
        'Hint: To disregard whether the collection supports the current version of '
        'ansible-core, configure COLLECTIONS_ON_ANSIBLE_VERSION_MISMATCH as "ignore".'
    )

    collection_dep_resolver = build_collection_dependency_resolver(
        galaxy_apis=galaxy_apis,
        concrete_artifacts_manager=concrete_artifacts_manager,
        preferred_candidates=preferred_candidates,
        with_deps=not no_deps,
        with_pre_releases=allow_pre_release,
        upgrade=upgrade,
        include_signatures=include_signatures,
        offline=offline,
    )
    try:
        return t.cast(
            dict[str, Candidate],
            collection_dep_resolver.resolve(
                requested_requirements,
                max_rounds=2000000,  # NOTE: same constant pip uses
            ).mapping,
        )
    except CollectionDependencyResolutionImpossible as dep_exc:
        conflict_causes = []
        for req_inf in dep_exc.causes:
            if req_inf.requirement.type == "requires_ansible":
                if req_inf.requirement.has_candidate:
                    continue
                collection = str(req_inf.parent)
                parents = [str(r._parent) for r in req_inf.parent._requirements if r._parent is not None]
                if not parents:
                    dep_origin = 'direct request'
                else:
                    dep_origin = f'dependency of {", ".join(parents)}'
            else:
                collection = str(req_inf.requirement)
                dep_origin = 'direct request' if req_inf.parent is None else f'dependency of {req_inf.parent!s}'

            cause = f"* {collection} ({dep_origin})"
            if req_inf.requirement.type == "requires_ansible":
                cause += f" requires {req_inf.requirement.fqcn!s} {req_inf.requirement.ver!s}"

            conflict_causes.append(cause)

        error_msg_lines = list(chain(
            (
                'Failed to resolve the requested '
                'dependencies map. Could not satisfy the following '
                'requirements:',
            ),
            conflict_causes,
        ))
        if any(req_inf.requirement.type == "requires_ansible" for req_inf in dep_exc.causes):
            dep_exc = None
            error_msg_lines.append(requires_ansible_hint)
        error_msg_lines.append(pre_release_hint)
        raise AnsibleError('\n'.join(error_msg_lines)) from dep_exc
    except CollectionDependencyInconsistentCandidate as dep_exc:
        parents = [
            str(p) for p in dep_exc.criterion.iter_parent()
            if p is not None
        ]

        error_msg_lines = [
            (
                'Failed to resolve the requested dependencies map. '
                'Got the candidate {req.fqcn!s}:{req.ver!s} ({dep_origin!s}) '
                'which didn\'t satisfy all of the following requirements:'.
                format(
                    req=dep_exc.candidate,
                    dep_origin='direct request'
                    if not parents else 'dependency of {parent!s}'.
                    format(parent=', '.join(parents))
                )
            )
        ]

        for req in dep_exc.criterion.iter_requirement():
            error_msg_lines.append(
                f'* {req.fqcn!s}:{req.ver!s}'
            )
        error_msg_lines.append(pre_release_hint)

        raise AnsibleError('\n'.join(error_msg_lines)) from dep_exc
    except ValueError as exc:
        raise AnsibleError(to_native(exc)) from exc
def _find_matches(self, requirements: list[Requirement]) -> list[Candidate]:
        # FIXME: The first requirement may be a Git repo followed by
        # FIXME: its cloned tmp dir. Using only the first one creates
        # FIXME: loops that prevent any further dependency exploration.
        # FIXME: We need to figure out how to prevent this.
        first_req = requirements[0]
        fqcn = first_req.fqcn
        # The fqcn is guaranteed to be the same
        version_req = "A SemVer-compliant version or '*' is required. See https://semver.org to learn how to compose it correctly. "
        version_req += "This is an issue with the collection."

        if first_req.type == "requires_ansible":
            for r in requirements:
                if r.has_candidate is None:
                    return []
            return [first_req.has_candidate]

        # If we're upgrading collections, we can't calculate preinstalled_candidates until the latest matches are found.
        # Otherwise, we can potentially avoid a Galaxy API call by doing this first.
        preinstalled_candidates = set()
        if not self._upgrade and first_req.type == 'galaxy':
            preinstalled_candidates = {
                candidate for candidate in self._preferred_candidates
                if candidate.fqcn == fqcn and
                all(self.is_satisfied_by(requirement, candidate) for requirement in requirements)
            }
        try:
            coll_versions: _c.Iterable[tuple[str, GalaxyAPI]] = (
                [] if preinstalled_candidates
                else self._api_proxy.get_collection_versions(first_req)
            )
        except TypeError as exc:
            if first_req.is_concrete_artifact:
                # Non hashable versions will cause a TypeError
                raise ValueError(
                    f"Invalid version found for the collection '{first_req}'. {version_req}"
                ) from exc
            # Unexpected error from a Galaxy server
            raise

        if first_req.is_concrete_artifact:
            # FIXME: do we assume that all the following artifacts are also concrete?
            # FIXME: does using fqcn==None cause us problems here?

            # Ensure the version found in the concrete artifact is SemVer-compliant
            for version, req_src in coll_versions:
                version_err = f"Invalid version found for the collection '{first_req}': {version} ({type(version)}). {version_req}"
                # NOTE: The known cases causing the version to be a non-string object come from
                # NOTE: the differences in how the YAML parser normalizes ambiguous values and
                # NOTE: how the end-users sometimes expect them to be parsed. Unless the users
                # NOTE: explicitly use the double quotes of one of the multiline string syntaxes
                # NOTE: in the collection metadata file, PyYAML will parse a value containing
                # NOTE: two dot-separated integers as `float`, a single integer as `int`, and 3+
                # NOTE: integers as a `str`. In some cases, they may also use an empty value
                # NOTE: which is normalized as `null` and turned into `None` in the Python-land.
                # NOTE: Another known mistake is setting a minor part of the SemVer notation
                # NOTE: skipping the "patch" bit like "1.0" which is assumed non-compliant even
                # NOTE: after the conversion to string.
                if not isinstance(version, str):
                    raise ValueError(version_err)
                elif version != '*':
                    try:
                        SemanticVersion(version)
                    except ValueError as ex:
                        raise ValueError(version_err) from ex

            return [
                Candidate(fqcn, version, _none_src_server, first_req.type, None)
                for version, _none_src_server in coll_versions
            ]

        latest_matches = []
        signatures = []
        extra_signature_sources: list[str] = []

        discarding_pre_releases_acceptable = any(
            not is_pre_release(candidate_version)
            for candidate_version, _src_server in coll_versions
        )

        # NOTE: The optimization of conditionally looping over the requirements
        # NOTE: is used to skip having to compute the pinned status of all
        # NOTE: requirements and apply version normalization to the found ones.
        all_pinned_requirement_version_numbers = {
            # NOTE: Pinned versions can start with a number, but also with an
            # NOTE: equals sign. Stripping it at the beginning should be
            # NOTE: enough. If there's a space after equals, the second strip
            # NOTE: will take care of it.
            # NOTE: Without this conversion, requirements versions like
            # NOTE: '1.2.3-alpha.4' work, but '=1.2.3-alpha.4' don't.
            requirement.ver.lstrip('=').strip()
            for requirement in requirements
            if requirement.is_pinned
        } if discarding_pre_releases_acceptable else set()

        for version, src_server in coll_versions:
            tmp_candidate = Candidate(fqcn, version, src_server, 'galaxy', None)

            for requirement in requirements:
                candidate_satisfies_requirement = self.is_satisfied_by(
                    requirement, tmp_candidate,
                )
                if not candidate_satisfies_requirement:
                    break

                should_disregard_pre_release_candidate = (
                    # NOTE: Do not discard pre-release candidates in the
                    # NOTE: following cases:
                    # NOTE:   * the end-user requested pre-releases explicitly;
                    # NOTE:   * the candidate is a concrete artifact (e.g. a
                    # NOTE:     Git repository, subdirs, a tarball URL, or a
                    # NOTE:     local dir or file etc.);
                    # NOTE:   * the candidate's pre-release version exactly
                    # NOTE:     matches a version specifically requested by one
                    # NOTE:     of the requirements in the current match
                    # NOTE:     discovery round (i.e. matching a requirement
                    # NOTE:     that is not a range but an explicit specific
                    # NOTE:     version pin). This works when some requirements
                    # NOTE:     request version ranges but others (possibly on
                    # NOTE:     different dependency tree level depths) demand
                    # NOTE:     pre-release dependency versions, even if those
                    # NOTE:     dependencies are transitive.
                    is_pre_release(tmp_candidate.ver)
                    and discarding_pre_releases_acceptable
                    and not (
                        self._with_pre_releases
                        or tmp_candidate.is_concrete_artifact
                        or version in all_pinned_requirement_version_numbers
                    )
                )
                if should_disregard_pre_release_candidate:
                    break

                # FIXME
                # candidate_is_from_requested_source = (
                #    requirement.src is None  # if this is true for some candidates but not all it will break key param - Nonetype can't be compared to str
                #    or requirement.src == candidate.src
                # )
                # if not candidate_is_from_requested_source:
                #     break

                if not self._include_signatures:
                    continue

                extra_signature_sources.extend(requirement.signature_sources or [])

            else:  # candidate satisfies requirements, `break` never happened
                if self._include_signatures:
                    for extra_source in extra_signature_sources:
                        signatures.append(get_signature_from_source(extra_source))
                latest_matches.append(
                    Candidate(fqcn, version, src_server, 'galaxy', frozenset(signatures))
                )

        latest_matches.sort(
            key=lambda candidate: (
                SemanticVersion(candidate.ver), candidate.src,
            ),
            reverse=True,  # prefer newer versions over older ones
        )

        if not preinstalled_candidates:
            preinstalled_candidates = {
                candidate for candidate in self._preferred_candidates
                if candidate.fqcn == fqcn and
                (
                    # check if an upgrade is necessary
                    all(self.is_satisfied_by(requirement, candidate) for requirement in requirements) and
                    (
                        not self._upgrade or
                        # check if an upgrade is preferred
                        all(SemanticVersion(latest.ver) <= SemanticVersion(candidate.ver) for latest in latest_matches)
                    )
                )
            }

        return list(preinstalled_candidates) + latest_matches
def from_string(
        cls,
        collection_input: str,
        artifacts_manager: ConcreteArtifactsManager,
        supplemental_signatures: list[str] | None,
    ) -> t.Self:
        req: dict[str, str | list[str] | None] = {}
        if _is_concrete_artifact_pointer(collection_input) or AnsibleCollectionRef.is_valid_collection_name(collection_input):
            # Arg is a file path or URL to a collection, or just a collection
            req['name'] = collection_input
        elif ':' in collection_input:
            req['name'], _sep, req['version'] = collection_input.partition(':')
            if not req['version']:
                del req['version']
        else:
            if not _glx_coll_mod.HAS_PACKAGING:
                raise AnsibleError("Failed to import packaging, check that a supported version is installed")
            try:
                pkg_req = _glx_coll_mod.PkgReq(collection_input)
            except Exception as e:
                # packaging doesn't know what this is, let it fly, better errors happen in from_requirement_dict
                req['name'] = collection_input
            else:
                req['name'] = pkg_req.name
                if pkg_req.specifier:
                    req['version'] = to_text(pkg_req.specifier)
        req['signatures'] = supplemental_signatures

        return cls.from_requirement_dict(req, artifacts_manager)
def _require_one_of_collections_requirements(
            self, collections, requirements_file,
            signatures=None,
            artifacts_manager=None,
    ):
        if collections and requirements_file:
            raise AnsibleError("The positional collection_name arg and --requirements-file are mutually exclusive.")
        elif not collections and not requirements_file:
            raise AnsibleError("You must specify a collection name or a requirements file.")
        elif requirements_file:
            if signatures is not None:
                raise AnsibleError(
                    "The --signatures option and --requirements-file are mutually exclusive. "
                    "Use the --signatures with positional collection_name args or provide a "
                    "'signatures' key for requirements in the --requirements-file."
                )
            requirements_file = GalaxyCLI._resolve_path(requirements_file)
            requirements = self._parse_requirements_file(
                requirements_file,
                allow_old_format=False,
                artifacts_manager=artifacts_manager,
            )
        else:
            requirements = {
                'collections': [
                    Requirement.from_string(coll_input, artifacts_manager, signatures)
                    for coll_input in collections
                ],
                'roles': [],
            }
        return requirements
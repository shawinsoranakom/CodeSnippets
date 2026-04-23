def get_direct_requires_ansible(self, collection: Candidate) -> str | None:
        """Extract requires_ansible from the on-disk collection artifact."""
        if collection.is_concrete_artifact:
            b_artifact_path = self.get_artifact_path(collection)
        else:
            b_artifact_path = self.get_galaxy_artifact_path(collection)

        if collection.is_url or collection.is_file or collection.is_online_index_pointer:
            runtime = _get_runtime_from_tar(b_artifact_path) or {}
        elif collection.is_dir:
            runtime = _get_runtime_from_dir(b_artifact_path) or {}
        elif collection.is_virtual:
            runtime = {}

        if not isinstance(runtime, Mapping):
            raise AnsibleError(
                f"The collection {collection} (type {collection.type}) (from {collection.src}) "
                "has an invalid meta/runtime.yml metadata. This file must contain a YAML dictionary."
            )
        if "requires_ansible" in runtime and not isinstance(runtime["requires_ansible"], str):
            raise AnsibleError(
                f"The collection {collection} (type {collection.type}) from {collection.src}) "
                "has invalid meta/runtime.yml metadata. The value for requires_ansible must be a string."
            )
        # NOTE: Using None as a sentinel since it's not a valid value otherwise.
        return runtime.get("requires_ansible")
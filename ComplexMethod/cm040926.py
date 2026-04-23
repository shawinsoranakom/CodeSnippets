def backend_update_secret_version_stage(
    fn, self, secret_id, version_stage, remove_from_version_id, move_to_version_id
):
    fn(self, secret_id, version_stage, remove_from_version_id, move_to_version_id)

    secret = self.secrets[secret_id]

    # Patch: default version is the new AWSCURRENT version
    if version_stage == AWSCURRENT:
        secret.default_version_id = move_to_version_id

    versions_no_stages = []
    for version_id, version in secret.versions.items():
        version_stages = version["version_stages"]

        # moto appends a new AWSPREVIOUS label to the version AWSCURRENT was removed from,
        # but it does not remove the old AWSPREVIOUS label.
        # Patch: ensure only one AWSPREVIOUS tagged version is in the pool.
        if (
            version_stage == AWSCURRENT
            and version_id != remove_from_version_id
            and AWSPREVIOUS in version_stages
        ):
            version_stages.remove(AWSPREVIOUS)

        if not version_stages:
            versions_no_stages.append(version_id)

    # Patch: remove secret versions with no version stages.
    for version_no_stages in versions_no_stages:
        del secret.versions[version_no_stages]

    return secret.arn, secret.name
def moto_smb_list_secret_version_ids(
    _, self, secret_id: str, include_deprecated: bool, *args, **kwargs
):
    if secret_id not in self.secrets:
        raise SecretNotFoundException()

    if self.secrets[secret_id].is_deleted():
        raise InvalidRequestException(
            "An error occurred (InvalidRequestException) when calling the UpdateSecret operation: "
            "You can't perform this operation on the secret because it was marked for deletion."
        )

    secret = self.secrets[secret_id]

    # Patch: output format, report exact createdate instead of current time.
    versions: list[SecretVersionsListEntry] = []
    for version_id, version in secret.versions.items():
        version_stages = version["version_stages"]
        # Patch: include deprecated versions if include_deprecated is True.
        # version_stages is empty if the version is deprecated.
        # see: https://docs.aws.amazon.com/secretsmanager/latest/userguide/getting-started.html#term_version
        if len(version_stages) > 0 or include_deprecated:
            entry = SecretVersionsListEntry(
                CreatedDate=version["createdate"],
                VersionId=version_id,
            )

            if version_stages:
                entry["VersionStages"] = version_stages

            # Patch: bind LastAccessedDate if one exists for this version.
            last_accessed_date = version.get("last_accessed_date")
            if last_accessed_date:
                entry["LastAccessedDate"] = last_accessed_date

            versions.append(entry)

    # Patch: sort versions by date.
    versions.sort(key=lambda v: v["CreatedDate"], reverse=True)

    response = ListSecretVersionIdsResponse(ARN=secret.arn, Name=secret.name, Versions=versions)

    return json.dumps(response)
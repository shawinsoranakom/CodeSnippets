def _convert_pr_to_document(
    pull_request: PullRequest, repo_external_access: ExternalAccess | None
) -> Document:
    repo_name = pull_request.base.repo.full_name if pull_request.base else ""
    doc_metadata = DocMetadata(repo=repo_name)
    file_content_byte = pull_request.body.encode('utf-8') if pull_request.body else b""
    name = sanitize_filename(pull_request.title, "md")

    return Document(
        id=pull_request.html_url,
        blob= file_content_byte,
        source=DocumentSource.GITHUB,
        external_access=repo_external_access,
        semantic_identifier=f"{pull_request.number}:{name}",
        # updated_at is UTC time but is timezone unaware, explicitly add UTC
        # as there is logic in indexing to prevent wrong timestamped docs
        # due to local time discrepancies with UTC
        doc_updated_at=(
            pull_request.updated_at.replace(tzinfo=timezone.utc)
            if pull_request.updated_at
            else None
        ),
        extension=".md",
        # this metadata is used in perm sync
        size_bytes=len(file_content_byte) if file_content_byte else 0,
        primary_owners=[],
        doc_metadata=doc_metadata.model_dump(),
        metadata={
            k: [str(vi) for vi in v] if isinstance(v, list) else str(v)
            for k, v in {
                "object_type": "PullRequest",
                "id": pull_request.number,
                "merged": pull_request.merged,
                "state": pull_request.state,
                "user": _get_userinfo(pull_request.user) if pull_request.user else None,
                "assignees": [
                    _get_userinfo(assignee) for assignee in pull_request.assignees
                ],
                "repo": (
                    pull_request.base.repo.full_name if pull_request.base else None
                ),
                "num_commits": str(pull_request.commits),
                "num_files_changed": str(pull_request.changed_files),
                "labels": [label.name for label in pull_request.labels],
                "created_at": (
                    pull_request.created_at.replace(tzinfo=timezone.utc)
                    if pull_request.created_at
                    else None
                ),
                "updated_at": (
                    pull_request.updated_at.replace(tzinfo=timezone.utc)
                    if pull_request.updated_at
                    else None
                ),
                "closed_at": (
                    pull_request.closed_at.replace(tzinfo=timezone.utc)
                    if pull_request.closed_at
                    else None
                ),
                "merged_at": (
                    pull_request.merged_at.replace(tzinfo=timezone.utc)
                    if pull_request.merged_at
                    else None
                ),
                "merged_by": (
                    _get_userinfo(pull_request.merged_by)
                    if pull_request.merged_by
                    else None
                ),
            }.items()
            if v is not None
        },
    )
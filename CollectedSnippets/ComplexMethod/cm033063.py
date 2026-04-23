def _convert_issue_to_document(
    issue: Issue, repo_external_access: ExternalAccess | None
) -> Document:
    repo_name = issue.repository.full_name if issue.repository else ""
    doc_metadata = DocMetadata(repo=repo_name)
    file_content_byte = issue.body.encode('utf-8') if issue.body else b""
    name = sanitize_filename(issue.title, "md")

    return Document(
        id=issue.html_url,
        blob=file_content_byte,
        source=DocumentSource.GITHUB,
        extension=".md",
        external_access=repo_external_access,
        semantic_identifier=f"{issue.number}:{name}",
        # updated_at is UTC time but is timezone unaware
        doc_updated_at=issue.updated_at.replace(tzinfo=timezone.utc),
        # this metadata is used in perm sync
        doc_metadata=doc_metadata.model_dump(),
        size_bytes=len(file_content_byte) if file_content_byte else 0,
        primary_owners=[_get_userinfo(issue.user) if issue.user else None],
        metadata={
            k: [str(vi) for vi in v] if isinstance(v, list) else str(v)
            for k, v in {
                "object_type": "Issue",
                "id": issue.number,
                "state": issue.state,
                "user": _get_userinfo(issue.user) if issue.user else None,
                "assignees": [_get_userinfo(assignee) for assignee in issue.assignees],
                "repo": issue.repository.full_name if issue.repository else None,
                "labels": [label.name for label in issue.labels],
                "created_at": (
                    issue.created_at.replace(tzinfo=timezone.utc)
                    if issue.created_at
                    else None
                ),
                "updated_at": (
                    issue.updated_at.replace(tzinfo=timezone.utc)
                    if issue.updated_at
                    else None
                ),
                "closed_at": (
                    issue.closed_at.replace(tzinfo=timezone.utc)
                    if issue.closed_at
                    else None
                ),
                "closed_by": (
                    _get_userinfo(issue.closed_by) if issue.closed_by else None
                ),
            }.items()
            if v is not None
        },
    )
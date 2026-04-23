def map_pr_to_document(pr: dict[str, Any], workspace: str, repo_slug: str) -> Document:
    """Map a Bitbucket pull request JSON to Onyx Document."""
    pr_id = pr["id"]
    title = pr.get("title") or f"PR {pr_id}"
    description = pr.get("description") or ""
    state = pr.get("state")
    draft = pr.get("draft", False)
    author = pr.get("author", {})
    reviewers = pr.get("reviewers", [])
    participants = pr.get("participants", [])

    link = pr.get("links", {}).get("html", {}).get("href") or (
        f"https://bitbucket.org/{workspace}/{repo_slug}/pull-requests/{pr_id}"
    )

    created_on = pr.get("created_on")
    updated_on = pr.get("updated_on")
    updated_dt = (
        datetime.fromisoformat(updated_on.replace("Z", "+00:00")).astimezone(
            timezone.utc
        )
        if isinstance(updated_on, str)
        else None
    )

    source_branch = pr.get("source", {}).get("branch", {}).get("name", "")
    destination_branch = pr.get("destination", {}).get("branch", {}).get("name", "")

    approved_by = [
        _get_user_name(p.get("user", {})) for p in participants if p.get("approved")
    ]

    primary_owner = None
    if author:
        primary_owner = BasicExpertInfo(
            display_name=_get_user_name(author),
        )

    # secondary_owners = [ 
    #     BasicExpertInfo(display_name=_get_user_name(r)) for r in reviewers
    # ] or None 

    reviewer_names = [_get_user_name(r) for r in reviewers]

    # Create a concise summary of key PR info
    created_date = created_on.split("T")[0] if created_on else "N/A"
    updated_date = updated_on.split("T")[0] if updated_on else "N/A"
    content_text = (
        "Pull Request Information:\n"
        f"- Pull Request ID: {pr_id}\n"
        f"- Title: {title}\n"
        f"- State: {state or 'N/A'} {'(Draft)' if draft else ''}\n"
    )
    if state == "DECLINED":
        content_text += f"- Reason: {pr.get('reason', 'N/A')}\n"
    content_text += (
        f"- Author: {_get_user_name(author) if author else 'N/A'}\n"
        f"- Reviewers: {', '.join(reviewer_names) if reviewer_names else 'N/A'}\n"
        f"- Branch: {source_branch} -> {destination_branch}\n"
        f"- Created: {created_date}\n"
        f"- Updated: {updated_date}"
    )
    if description:
        content_text += f"\n\nDescription:\n{description}"

    metadata: dict[str, str | list[str]] = {
        "object_type": "PullRequest",
        "workspace": workspace,
        "repository": repo_slug,
        "pr_key": f"{workspace}/{repo_slug}#{pr_id}",
        "id": str(pr_id),
        "title": title,
        "state": state or "",
        "draft": str(bool(draft)),
        "link": link,
        "author": _get_user_name(author) if author else "",
        "reviewers": reviewer_names,
        "approved_by": approved_by,
        "comment_count": str(pr.get("comment_count", "")),
        "task_count": str(pr.get("task_count", "")),
        "created_on": created_on or "",
        "updated_on": updated_on or "",
        "source_branch": source_branch,
        "destination_branch": destination_branch,
        "closed_by": (
            _get_user_name(pr.get("closed_by", {})) if pr.get("closed_by") else ""
        ),
        "close_source_branch": str(bool(pr.get("close_source_branch", False))),
    }

    name = sanitize_filename(title, "md")

    return Document(
        id=f"{DocumentSource.BITBUCKET.value}:{workspace}:{repo_slug}:pr:{pr_id}",
        blob=content_text.encode("utf-8"),
        source=DocumentSource.BITBUCKET,
        extension=".md",
        semantic_identifier=f"#{pr_id}: {name}",
        size_bytes=len(content_text.encode("utf-8")),
        doc_updated_at=updated_dt,
        primary_owners=[primary_owner] if primary_owner else None,
        # secondary_owners=secondary_owners,
        metadata=metadata,
    )
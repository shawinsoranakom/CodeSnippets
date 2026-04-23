def main(config: dict[str, Any] | None = None) -> None:
    if config is None:
        args = _build_arg_parser().parse_args()
        config = {
            "base_url": args.base_url,
            "project_key": args.project_key,
            "jql_query": args.jql_query,
            "batch_size": args.batch_size,
            "start_ts": args.start_ts,
            "end_ts": args.end_ts,
            "include_comments": args.include_comments,
            "include_attachments": args.include_attachments,
            "attachment_size_limit": args.attachment_size_limit,
            "credentials": {
                "jira_user_email": args.user_email,
                "jira_api_token": args.api_token,
                "jira_password": args.password,
            },
        }

    base_url = config.get("base_url")
    credentials = config.get("credentials", {})

    if not base_url:
        raise RuntimeError("Jira base URL must be provided via config or CLI arguments.")
    if not (credentials.get("jira_api_token") or (credentials.get("jira_user_email") and credentials.get("jira_password"))):
        raise RuntimeError("Provide either an API token or both email/password for Jira authentication.")

    connector_options = {
        key: value
        for key, value in (
            ("include_comments", config.get("include_comments")),
            ("include_attachments", config.get("include_attachments")),
            ("attachment_size_limit", config.get("attachment_size_limit")),
            ("labels_to_skip", config.get("labels_to_skip")),
            ("comment_email_blacklist", config.get("comment_email_blacklist")),
            ("scoped_token", config.get("scoped_token")),
            ("timezone_offset", config.get("timezone_offset")),
        )
        if value is not None
    }

    documents = test_jira(
        base_url=base_url,
        project_key=config.get("project_key"),
        jql_query=config.get("jql_query"),
        credentials=credentials,
        batch_size=config.get("batch_size", INDEX_BATCH_SIZE),
        start_ts=config.get("start_ts"),
        end_ts=config.get("end_ts"),
        connector_options=connector_options,
    )

    preview_count = min(len(documents), 5)
    for idx in range(preview_count):
        doc = documents[idx]
        print(f"[Jira] [Sample {idx + 1}] {doc.semantic_identifier} | id={doc.id} | size={doc.size_bytes} bytes")

    print(f"[Jira] Jira connector test completed. Documents fetched: {len(documents)}")
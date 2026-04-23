def _article_to_document(
    article: dict[str, Any],
    content_tags: dict[str, str],
    author_map: dict[str, BasicExpertInfo],
    client: ZendeskClient,
) -> tuple[dict[str, BasicExpertInfo] | None, Document]:
    author_id = article.get("author_id")
    if not author_id:
        author = None
    else:
        author = (
            author_map.get(author_id)
            if author_id in author_map
            else _fetch_author(client, author_id)
        )

    new_author_mapping = {author_id: author} if author_id and author else None

    updated_at = article.get("updated_at")
    update_time = time_str_to_utc(updated_at) if updated_at else None

    text = parse_html_page_basic(article.get("body") or "")
    blob = text.encode("utf-8", errors="replace")
    # Build metadata
    metadata: dict[str, str | list[str]] = {
        "labels": [str(label) for label in article.get("label_names", []) if label],
        "content_tags": [
            content_tags[tag_id]
            for tag_id in article.get("content_tag_ids", [])
            if tag_id in content_tags
        ],
    }

    # Remove empty values
    metadata = {k: v for k, v in metadata.items() if v}

    return new_author_mapping, Document(
        id=f"article:{article['id']}",
        source=DocumentSource.ZENDESK,
        semantic_identifier=article["title"],
        extension=".txt",
        blob=blob,
        size_bytes=len(blob),
        doc_updated_at=update_time,
        primary_owners=[author] if author else None,
        metadata=metadata,
    )
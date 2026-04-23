def convert_drive_item_to_document(
    creds: Any,
    allow_images: bool,
    size_threshold: int,
    # if not specified, we will not sync permissions
    # will also be a no-op if EE is not enabled
    permission_sync_context: PermissionSyncContext | None,
    retriever_emails: list[str],
    file: GoogleDriveFileType,
) -> Document | ConnectorFailure | None:
    """
    Attempt to convert a drive item to a document with each retriever email
    in order. returns upon a successful retrieval or a non-403 error.

    We used to always get the user email from the file owners when available,
    but this was causing issues with shared folders where the owner was not included in the service account
    now we use the email of the account that successfully listed the file. There are cases where a
    user that can list a file cannot download it, so we retry with file owners and admin email.
    """
    first_error = None
    doc_or_failure = None
    retriever_emails = retriever_emails[:MAX_RETRIEVER_EMAILS]
    # use seen instead of list(set()) to avoid re-ordering the retriever emails
    seen = set()
    for retriever_email in retriever_emails:
        if retriever_email in seen:
            continue
        seen.add(retriever_email)
        doc_or_failure = _convert_drive_item_to_document(
            creds,
            allow_images,
            size_threshold,
            retriever_email,
            file,
            permission_sync_context,
        )

        # There are a variety of permissions-based errors that occasionally occur
        # when retrieving files. Often when these occur, there is another user
        # that can successfully retrieve the file, so we try the next user.
        if doc_or_failure is None or isinstance(doc_or_failure, Document) or not (isinstance(doc_or_failure.exception, HttpError) and doc_or_failure.exception.status_code in [401, 403, 404]):
            return doc_or_failure

        if first_error is None:
            first_error = doc_or_failure
        else:
            first_error.failure_message += f"\n\n{doc_or_failure.failure_message}"

    if first_error and isinstance(first_error.exception, HttpError) and first_error.exception.status_code == 403:
        # This SHOULD happen very rarely, and we don't want to break the indexing process when
        # a high volume of 403s occurs early. We leave a verbose log to help investigate.
        logging.error(
            f"Skipping file id: {file.get('id')} name: {file.get('name')} due to 403 error.Attempted to retrieve with {retriever_emails},got the following errors: {first_error.failure_message}"
        )
        return None
    return first_error
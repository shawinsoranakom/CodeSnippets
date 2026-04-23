def submit_parse_task_sync(
    base_url: str,
    upload_assets: Sequence[UploadAsset],
    form_data: dict[str, str | list[str]],
) -> SubmitResponse:
    with httpx.Client(timeout=build_http_timeout(), follow_redirects=True) as sync_client:
        with ExitStack() as stack:
            files = []
            for upload_asset in upload_assets:
                mime_type = (
                    mimetypes.guess_type(upload_asset.upload_name)[0]
                    or "application/octet-stream"
                )
                file_handle = stack.enter_context(open(upload_asset.path, "rb"))
                files.append(
                    (
                        "files",
                        (
                            upload_asset.upload_name,
                            file_handle,
                            mime_type,
                        ),
                    )
                )

            response = sync_client.post(
                f"{base_url}{TASKS_ENDPOINT}",
                data=form_data,
                files=files,
            )

    if response.status_code != 202:
        raise click.ClickException(
            f"Failed to submit parsing task: "
            f"{response.status_code} {response_detail(response)}"
        )

    payload = response.json()
    task_id = payload.get("task_id")
    status_url = payload.get("status_url")
    result_url = payload.get("result_url")
    file_names = payload.get("file_names")
    queued_ahead = payload.get("queued_ahead")
    if (
        not isinstance(task_id, str)
        or not isinstance(status_url, str)
        or not isinstance(result_url, str)
    ):
        raise click.ClickException("MinerU API returned an invalid task payload")

    normalized_file_names: tuple[str, ...] = ()
    if isinstance(file_names, list) and all(isinstance(name, str) for name in file_names):
        normalized_file_names = tuple(file_names)
    if not isinstance(queued_ahead, int):
        queued_ahead = None

    return SubmitResponse(
        task_id=task_id,
        status_url=status_url,
        result_url=result_url,
        file_names=normalized_file_names,
        queued_ahead=queued_ahead,
    )
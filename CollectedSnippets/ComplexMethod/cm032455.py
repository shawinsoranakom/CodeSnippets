def step_05_upload_files(
    flow_page,
    flow_state,
    base_url,
    login_url,
    active_auth_context,
    step,
    snap,
    auth_click,
    seeded_user_credentials,
    tmp_path,
    ensure_dataset_ready,
):
    require(flow_state, "dataset_name", "dataset_settings_done", "file_paths")
    page = flow_page
    file_paths = [Path(path) for path in flow_state["file_paths"]]
    filenames = flow_state.get("filenames") or [path.name for path in file_paths]
    flow_state["filenames"] = filenames

    for idx, file_path in enumerate(file_paths):
        filename = file_path.name
        with step(f"open upload modal for {filename}"):
            upload_modal = ensure_upload_modal_open(
                page, expect, auth_click, timeout_ms=RESULT_TIMEOUT_MS
            )
        if idx == 0:
            snap("upload_modal_open")

        with step(f"enable parse on creation for {filename}"):
            ensure_parse_on(upload_modal, expect)
        if idx == 0:
            snap("parse_toggle_on")

        with step(f"upload file {filename}"):
            upload_file(page, expect, upload_modal, str(file_path), RESULT_TIMEOUT_MS)
            expect(upload_modal.locator(f"text={filename}")).to_be_visible(
                timeout=RESULT_TIMEOUT_MS
            )

        with step(f"submit upload {filename}"):
            save_button = upload_modal.locator(
                "button", has_text=re.compile("save", re.I)
            ).first

            def trigger():
                save_button.click()

            capture_response(
                page,
                trigger,
                lambda resp: resp.request.method == "POST"
                and "/v1/document/upload" in resp.url,
            )
            expect(upload_modal).not_to_be_visible(timeout=RESULT_TIMEOUT_MS)
        snap(f"upload_{filename}_submitted")

        row = page.locator(
            f"[data-testid='document-row'][data-doc-name={json.dumps(filename)}]"
        )
        expect(row).to_be_visible(timeout=RESULT_TIMEOUT_MS)

    flow_state["uploads_done"] = True
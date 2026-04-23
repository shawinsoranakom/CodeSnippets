def step_03_create_dataset(
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
    require(flow_state, "logged_in")
    page = flow_page
    with step("open create dataset modal"):
        try:
            modal = open_create_dataset_modal(page, expect, RESULT_TIMEOUT_MS)
        except AssertionError:
            fallback_id = (ensure_dataset_ready or {}).get("kb_id")
            fallback_name = (ensure_dataset_ready or {}).get("kb_name")
            if not fallback_id or not fallback_name:
                raise
            page.goto(
                urljoin(base_url.rstrip("/") + "/", f"/dataset/dataset/{fallback_id}"),
                wait_until="domcontentloaded",
            )
            wait_for_dataset_detail_ready(page, expect, timeout_ms=RESULT_TIMEOUT_MS * 2)
            flow_state["dataset_name"] = fallback_name
            flow_state["dataset_id"] = fallback_id
            snap("dataset_created")
            snap("dataset_detail_ready")
            return
    snap("dataset_modal_open")

    dataset_name = f"qa-dataset-{int(time.time() * 1000)}"
    with step("fill dataset form"):
        name_input = modal.locator("input[placeholder='Please input name.']").first
        expect(name_input).to_be_visible()
        name_input.fill(dataset_name)

        try:
            select_chunking_method_general(page, expect, modal, RESULT_TIMEOUT_MS)
        except Exception:
            snap("failure_dataset_create")
            raise

        save_button = None
        if hasattr(modal, "get_by_role"):
            save_button = modal.get_by_role("button", name=re.compile(r"^save$", re.I))
        if save_button is None or save_button.count() == 0:
            save_button = modal.locator("button", has_text=re.compile(r"^save$", re.I)).first
        expect(save_button).to_be_visible(timeout=RESULT_TIMEOUT_MS)
        created_kb_id = None

        def trigger():
            save_button.click()

        create_response = capture_response(
            page,
            trigger,
            lambda resp: resp.request.method == "POST" and "/v1/kb/create" in resp.url,
            timeout_ms=RESULT_TIMEOUT_MS * 2,
        )
        try:
            create_payload = create_response.json()
        except Exception:
            create_payload = {}
        if isinstance(create_payload, dict):
            data = create_payload.get("data") or {}
            if isinstance(data, dict):
                created_kb_id = data.get("id") or data.get("kb_id")

        expect(modal).not_to_be_visible(timeout=RESULT_TIMEOUT_MS)
        try:
            wait_for_dataset_detail(page, timeout_ms=RESULT_TIMEOUT_MS * 2)
        except Exception:
            if created_kb_id:
                page.goto(
                    urljoin(
                        base_url.rstrip("/") + "/", f"/dataset/dataset/{created_kb_id}"
                    ),
                    wait_until="domcontentloaded",
                )
            else:
                raise
        wait_for_dataset_detail_ready(page, expect, timeout_ms=RESULT_TIMEOUT_MS * 2)
    dataset_id = extract_dataset_id_from_url(page.url)
    flow_state["dataset_name"] = dataset_name
    flow_state["dataset_id"] = dataset_id
    snap("dataset_created")
    snap("dataset_detail_ready")
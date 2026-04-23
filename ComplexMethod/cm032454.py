def step_04_set_dataset_settings(
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
    require(flow_state, "dataset_name", "dataset_id")
    page = flow_page
    dataset_id = flow_state["dataset_id"]
    dataset_name = flow_state["dataset_name"]
    metadata_field_key = "auto_meta_field"

    with step("open dataset settings page"):
        page.goto(
            urljoin(
                base_url.rstrip("/") + "/", f"/dataset/dataset-setting/{dataset_id}"
            ),
            wait_until="domcontentloaded",
        )
        expect(page.get_by_test_id("ds-settings-basic-name-input")).to_be_visible(
            timeout=RESULT_TIMEOUT_MS
        )
        expect(page.get_by_test_id("ds-settings-page-save-btn")).to_be_visible(
            timeout=RESULT_TIMEOUT_MS
        )
    snap("dataset_settings_open")

    with step("fill base settings"):
        page.get_by_test_id("ds-settings-basic-name-input").fill(
            f"{dataset_name}-cfg"
        )
        select_combobox_option(
            page, "ds-settings-basic-language-select", preferred_text="English"
        )

        avatar_path = make_test_png(tmp_path / "avatar-test.png")
        page.get_by_test_id("ds-settings-basic-avatar-upload").set_input_files(
            str(avatar_path)
        )
        crop_modal = page.get_by_test_id("ds-settings-basic-avatar-crop-modal")
        expect(crop_modal).to_be_visible(timeout=RESULT_TIMEOUT_MS)
        page.get_by_test_id("ds-settings-basic-avatar-crop-confirm-btn").click()
        expect(crop_modal).not_to_be_visible(timeout=RESULT_TIMEOUT_MS)

        page.get_by_test_id("ds-settings-basic-description-input").fill(
            "Dataset setting playwright description"
        )
        try:
            select_combobox_option(page, "ds-settings-basic-permissions-select")
        except Exception:
            page.keyboard.press("Escape")

        embedding_trigger = page.get_by_test_id(
            "ds-settings-basic-embedding-model-select"
        ).first
        expect(embedding_trigger).to_be_visible(timeout=RESULT_TIMEOUT_MS)
        if not embedding_trigger.is_disabled():
            try:
                select_combobox_option(page, "ds-settings-basic-embedding-model-select")
            except Exception:
                page.keyboard.press("Escape")

    with step("fill parser and metadata settings"):
        set_number_input(page, "ds-settings-parser-page-rank-input", 12)
        select_combobox_option(
            page, "ds-settings-parser-pdf-parser-select", preferred_text="Plain Text"
        )
        set_number_input(page, "ds-settings-parser-recommended-chunk-size-input", 640)
        set_switch_state(page, "ds-settings-parser-child-chunk-switch", True)
        expect(
            page.get_by_test_id("ds-settings-parser-child-chunk-delimiter-input")
        ).to_be_visible(timeout=RESULT_TIMEOUT_MS)
        set_switch_state(page, "ds-settings-parser-page-index-switch", True)
        set_number_input(page, "ds-settings-parser-image-table-context-window-input", 16)
        set_switch_state(page, "ds-settings-metadata-switch", True)

        page.get_by_test_id("ds-settings-metadata-open-modal-btn").click()
        metadata_modal = page.get_by_test_id("ds-settings-metadata-modal")
        expect(metadata_modal).to_be_visible(timeout=RESULT_TIMEOUT_MS)
        page.get_by_test_id("ds-settings-metadata-add-btn").click()

        nested_modal = page.get_by_test_id("ds-settings-metadata-add-modal")
        expect(nested_modal).to_be_visible(timeout=RESULT_TIMEOUT_MS)
        field_input = nested_modal.locator("input[name='field']")
        if field_input.count() == 0:
            field_input = nested_modal.locator("input")
        expect(field_input.first).to_be_visible(timeout=RESULT_TIMEOUT_MS)
        field_input.first.fill(metadata_field_key)
        description_input = nested_modal.locator("textarea")
        if description_input.count() > 0:
            description_input.first.fill("auto metadata field from playwright")
        confirm_btn = page.get_by_test_id("ds-settings-metadata-add-modal-confirm-btn")
        confirm_btn.click()
        try:
            expect(nested_modal).not_to_be_visible(timeout=3000)
        except AssertionError:
            retry_field_input = nested_modal.locator("input[name='field']")
            if retry_field_input.count() > 0:
                retry_field_input.first.fill("auto_meta_field_retry")
            confirm_btn.click()
            expect(nested_modal).not_to_be_visible(timeout=RESULT_TIMEOUT_MS)
        snap("dataset_settings_metadata_modal")

        page.get_by_test_id("ds-settings-metadata-modal-save-btn").click()
        expect(metadata_modal).not_to_be_visible(timeout=RESULT_TIMEOUT_MS)

        overlap_slider = page.get_by_test_id(
            "ds-settings-parser-overlapped-percent-slider"
        ).first
        expect(overlap_slider).to_be_visible(timeout=RESULT_TIMEOUT_MS)
        overlap_slider.focus()
        overlap_slider.press("ArrowRight")
        set_number_input(page, "ds-settings-parser-auto-keyword-input", 3)
        set_number_input(page, "ds-settings-parser-auto-question-input", 2)
        set_switch_state(page, "ds-settings-parser-excel-to-html-switch", True)

    with step("fill graph and raptor settings"):
        page.get_by_test_id("ds-settings-graph-entity-types-add-btn").click()
        entity_input = page.get_by_test_id("ds-settings-graph-entity-types-input").first
        expect(entity_input).to_be_visible(timeout=RESULT_TIMEOUT_MS)
        entity_input.fill("playwright_entity")
        entity_input.press("Enter")
        select_ragflow_option(
            page, "ds-settings-graph-method-select", preferred_text="General"
        )
        set_switch_state(page, "ds-settings-graph-entity-resolution-switch", True)
        set_switch_state(page, "ds-settings-graph-community-reports-switch", True)

        raptor_scope_dataset = page.get_by_role(
            "radio", name=re.compile(r"^Dataset$", re.I)
        ).first
        raptor_scope_dataset.check(force=True)
        expect(raptor_scope_dataset).to_be_checked(timeout=RESULT_TIMEOUT_MS)
        page.get_by_test_id("ds-settings-raptor-prompt-textarea").fill(
            "Playwright prompt for dataset settings"
        )
        set_number_input(page, "ds-settings-raptor-max-token-input", 300)
        set_number_input(page, "ds-settings-raptor-threshold-input", 0.3)
        set_number_input(page, "ds-settings-raptor-max-cluster-input", 128)
        set_number_input(page, "ds-settings-raptor-seed-input", 1234)
        seed_input = page.get_by_test_id("ds-settings-raptor-seed-input").first
        seed_before_randomize = seed_input.input_value()
        page.get_by_test_id("ds-settings-raptor-seed-randomize-btn").click()
        page.wait_for_function(
            """([testId, previous]) => {
              const node = document.querySelector(`[data-testid="${testId}"]`);
              return !!node && String(node.value) !== String(previous);
            }""",
            arg=["ds-settings-raptor-seed-input", seed_before_randomize],
            timeout=RESULT_TIMEOUT_MS,
        )

    with step("save dataset settings and assert update payload"):
        try:
            expect(page.locator("[data-sonner-toast]")).to_have_count(0, timeout=8000)
        except AssertionError:
            pass
        save_btn = page.get_by_test_id("ds-settings-page-save-btn").first
        expect(save_btn).to_be_visible(timeout=RESULT_TIMEOUT_MS)

        def trigger():
            save_btn.click()

        response = capture_response(
            page,
            trigger,
            lambda resp: resp.request.method == "POST" and "/v1/kb/update" in resp.url,
            timeout_ms=RESULT_TIMEOUT_MS * 2,
        )
        assert 200 <= response.status < 400, f"Unexpected /v1/kb/update status={response.status}"
        response_payload = response.json()
        if isinstance(response_payload, dict):
            assert response_payload.get("code") == 0, (
                f"/v1/kb/update response code={response_payload.get('code')} "
                f"message={response_payload.get('message')}"
            )

        payload = get_request_json_payload(response)
        assert payload.get("kb_id") == dataset_id, (
            f"Expected kb_id={dataset_id!r}, got {payload.get('kb_id')!r}"
        )
        for key in ("name", "language", "parser_config"):
            assert key in payload, f"Expected key {key!r} in /v1/kb/update payload"
        parser_config = payload.get("parser_config") or {}
        assert (
            parser_config.get("image_table_context_window")
            == parser_config.get("image_context_size")
            == parser_config.get("table_context_size")
        ), "Expected image/table context window transform keys to be aligned"
        expect(page.locator("[data-sonner-toast]").first).to_be_visible(
            timeout=RESULT_TIMEOUT_MS
        )

    with step("return to dataset detail for upload"):
        page.goto(
            urljoin(base_url.rstrip("/") + "/", f"/dataset/dataset/{dataset_id}"),
            wait_until="domcontentloaded",
        )
        wait_for_dataset_detail_ready(page, expect, timeout_ms=RESULT_TIMEOUT_MS)

    flow_state["dataset_settings_done"] = True
    flow_state["settings_update_payload"] = payload
    snap("dataset_settings_saved")
def step_02_validate_page(ctx: FlowContext, step, snap):
    require(ctx.state, "smoke_opened")
    page = ctx.page
    response = ctx.state.get("smoke_response")
    content = page.content()
    content_type = ""
    status = None
    if response is not None:
        status = response.status
        content_type = response.headers.get("content-type", "")

    content_head = content.lstrip()[:200]
    looks_json = content_head.startswith("{") or content_head.startswith("[")
    is_html = "text/html" in content_type.lower() or "<html" in content.lower()

    if response is not None and status is not None and status >= 400:
        raise AssertionError(_format_diag(page, response, "HTTP error status"))

    if looks_json or not is_html:
        raise AssertionError(_format_diag(page, response, "Non-HTML response"))

    root_count = page.locator("#root").count()
    input_count = page.locator("input").count()
    logo_count = page.locator("img[alt='logo']").count()
    if root_count + input_count + logo_count == 0:
        raise AssertionError(
            _format_diag(page, response, "No SPA root, inputs, or logo found")
        )
def _write_artifacts_if_failed(page, context, request) -> None:
    report = getattr(request.node, "_rep_call", None)
    if not report or not report.failed:
        return

    timestamp = time.strftime("%Y%m%d-%H%M%S")
    base_dir = _request_artifacts_dir(request)
    safe_name = _request_artifact_prefix(request)
    screenshot_path = base_dir / f"{safe_name}_{timestamp}.png"
    html_path = base_dir / f"{safe_name}_{timestamp}.html"
    events_path = base_dir / f"{safe_name}_{timestamp}.log"
    trace_path = base_dir / f"{safe_name}_{timestamp}.zip"

    try:
        page.screenshot(path=str(screenshot_path), full_page=True)
    except Exception as exc:
        print(f"[artifact] screenshot failed: {exc}", flush=True)

    try:
        html_path.write_text(page.content(), encoding="utf-8")
    except Exception as exc:
        print(f"[artifact] html dump failed: {exc}", flush=True)

    try:
        lines = []
        diag = getattr(page, "_diag", {})
        for key in ("console_errors", "page_errors", "request_failed"):
            entries = diag.get(key, [])
            if entries:
                lines.append(f"{key}:")
                lines.extend(entries)
        if lines:
            events_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    except Exception as exc:
        print(f"[artifact] events dump failed: {exc}", flush=True)

    if getattr(context, "_trace_enabled", False) and not getattr(
        context, "_trace_saved", False
    ):
        try:
            context.tracing.stop(path=str(trace_path))
            context._trace_saved = True
        except Exception as exc:
            print(f"[artifact] trace dump failed: {exc}", flush=True)
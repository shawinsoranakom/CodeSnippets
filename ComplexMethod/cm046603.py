def _run_oxc_batch(
    *,
    node_lang: str,
    validation_mode: str,
    code_shape: str,
    code_values: list[str],
) -> list[dict[str, Any]]:
    if not _OXC_RUNNER_PATH.exists():
        return _fallback_results(
            len(code_values),
            f"OXC runner missing at {_OXC_RUNNER_PATH}",
        )

    payload = {
        "lang": node_lang,
        "mode": validation_mode,
        "code_shape": code_shape,
        "codes": code_values,
    }
    try:
        tmp_dir = ensure_dir(oxc_validator_tmp_root())
        env = dict(os.environ)
        tmp_dir_str = str(tmp_dir)
        env["TMPDIR"] = tmp_dir_str
        env["TMP"] = tmp_dir_str
        env["TEMP"] = tmp_dir_str
        proc = subprocess.run(
            ["node", str(_OXC_RUNNER_PATH)],
            cwd = str(_OXC_TOOL_DIR),
            input = json.dumps(payload),
            text = True,
            capture_output = True,
            check = False,
            env = env,
        )
    except (OSError, ValueError) as exc:
        logger.warning("OXC subprocess launch failed: %s", exc)
        return _fallback_results(len(code_values), f"OXC launch failed: {exc}")

    if proc.returncode != 0:
        message = (proc.stderr or proc.stdout or "unknown error").strip()
        if len(message) > 300:
            message = f"{message[:300]}..."
        return _fallback_results(len(code_values), f"OXC failed: {message}")

    try:
        raw = json.loads(proc.stdout)
    except json.JSONDecodeError:
        return _fallback_results(len(code_values), "OXC output parse failed.")

    if not isinstance(raw, list):
        return _fallback_results(len(code_values), "OXC output must be an array.")

    out: list[dict[str, Any]] = []
    for item in raw:
        if not isinstance(item, dict):
            out.append(
                {
                    "is_valid": False,
                    "error_count": 1,
                    "error_message": "Invalid OXC result entry.",
                    "severity": None,
                    "code": None,
                    "labels": [],
                    "codeframe": None,
                    "warning_count": 0,
                }
            )
            continue
        is_valid_raw = item.get("is_valid")
        error_count_raw = item.get("error_count")
        message_raw = item.get("error_message")
        severity_raw = item.get("severity")
        code_raw = item.get("code")
        labels_raw = item.get("labels")
        codeframe_raw = item.get("codeframe")
        warning_count_raw = item.get("warning_count")
        out.append(
            {
                "is_valid": bool(is_valid_raw)
                if isinstance(is_valid_raw, bool)
                else False,
                "error_count": int(error_count_raw)
                if isinstance(error_count_raw, int)
                else 0,
                "error_message": str(message_raw or ""),
                "severity": str(severity_raw)
                if isinstance(severity_raw, str)
                else None,
                "code": str(code_raw) if isinstance(code_raw, str) else None,
                "labels": labels_raw if isinstance(labels_raw, list) else [],
                "codeframe": str(codeframe_raw)
                if isinstance(codeframe_raw, str)
                else None,
                "warning_count": int(warning_count_raw)
                if isinstance(warning_count_raw, int)
                else 0,
            }
        )
    return out
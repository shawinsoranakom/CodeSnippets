def check_updates(id_task, disable_list):
    check_access()

    disabled = json.loads(disable_list)
    assert type(disabled) == list, f"wrong disable_list data for apply_and_restart: {disable_list}"

    exts = [ext for ext in extensions.extensions if ext.remote is not None and ext.name not in disabled]
    shared.state.job_count = len(exts)

    for ext in exts:
        shared.state.textinfo = ext.name

        try:
            ext.check_updates()
        except FileNotFoundError as e:
            if 'FETCH_HEAD' not in str(e):
                raise
        except Exception:
            errors.report(f"Error checking updates for {ext.name}", exc_info=True)

        shared.state.nextjob()

    return extension_table(), ""
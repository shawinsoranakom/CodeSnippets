def update_config_states_table(state_name):
    if state_name == "Current":
        config_state = config_states.get_config()
    else:
        config_state = config_states.all_config_states[state_name]

    config_name = config_state.get("name", "Config")
    created_date = datetime.fromtimestamp(config_state["created_at"]).strftime('%Y-%m-%d %H:%M:%S')
    filepath = config_state.get("filepath", "<unknown>")

    try:
        webui_remote = config_state["webui"]["remote"] or ""
        webui_branch = config_state["webui"]["branch"]
        webui_commit_hash = config_state["webui"]["commit_hash"] or "<unknown>"
        webui_commit_date = config_state["webui"]["commit_date"]
        if webui_commit_date:
            webui_commit_date = time.asctime(time.gmtime(webui_commit_date))
        else:
            webui_commit_date = "<unknown>"

        remote = f"""<a href="{html.escape(webui_remote)}" target="_blank">{html.escape(webui_remote or '')}</a>"""
        commit_link = make_commit_link(webui_commit_hash, webui_remote)
        date_link = make_commit_link(webui_commit_hash, webui_remote, webui_commit_date)

        current_webui = config_states.get_webui_config()

        style_remote = ""
        style_branch = ""
        style_commit = ""
        if current_webui["remote"] != webui_remote:
            style_remote = STYLE_PRIMARY
        if current_webui["branch"] != webui_branch:
            style_branch = STYLE_PRIMARY
        if current_webui["commit_hash"] != webui_commit_hash:
            style_commit = STYLE_PRIMARY

        code = f"""<!-- {time.time()} -->
<h2>Config Backup: {config_name}</h2>
<div><b>Filepath:</b> {filepath}</div>
<div><b>Created at:</b> {created_date}</div>
<h2>WebUI State</h2>
<table id="config_state_webui">
    <thead>
        <tr>
            <th>URL</th>
            <th>Branch</th>
            <th>Commit</th>
            <th>Date</th>
        </tr>
    </thead>
    <tbody>
        <tr>
            <td>
                <label{style_remote}>{remote}</label>
            </td>
            <td>
                <label{style_branch}>{webui_branch}</label>
            </td>
            <td>
                <label{style_commit}>{commit_link}</label>
            </td>
            <td>
                <label{style_commit}>{date_link}</label>
            </td>
        </tr>
    </tbody>
</table>
<h2>Extension State</h2>
<table id="config_state_extensions">
    <thead>
        <tr>
            <th>Extension</th>
            <th>URL</th>
            <th>Branch</th>
            <th>Commit</th>
            <th>Date</th>
        </tr>
    </thead>
    <tbody>
"""

        ext_map = {ext.name: ext for ext in extensions.extensions}

        for ext_name, ext_conf in config_state["extensions"].items():
            ext_remote = ext_conf["remote"] or ""
            ext_branch = ext_conf["branch"] or "<unknown>"
            ext_enabled = ext_conf["enabled"]
            ext_commit_hash = ext_conf["commit_hash"] or "<unknown>"
            ext_commit_date = ext_conf["commit_date"]
            if ext_commit_date:
                ext_commit_date = time.asctime(time.gmtime(ext_commit_date))
            else:
                ext_commit_date = "<unknown>"

            remote = f"""<a href="{html.escape(ext_remote)}" target="_blank">{html.escape(ext_remote or '')}</a>"""
            commit_link = make_commit_link(ext_commit_hash, ext_remote)
            date_link = make_commit_link(ext_commit_hash, ext_remote, ext_commit_date)

            style_enabled = ""
            style_remote = ""
            style_branch = ""
            style_commit = ""
            if ext_name in ext_map:
                current_ext = ext_map[ext_name]
                current_ext.read_info_from_repo()
                if current_ext.enabled != ext_enabled:
                    style_enabled = STYLE_PRIMARY
                if current_ext.remote != ext_remote:
                    style_remote = STYLE_PRIMARY
                if current_ext.branch != ext_branch:
                    style_branch = STYLE_PRIMARY
                if current_ext.commit_hash != ext_commit_hash:
                    style_commit = STYLE_PRIMARY

            code += f"""        <tr>
            <td><label{style_enabled}><input class="gr-check-radio gr-checkbox" type="checkbox" disabled="true" {'checked="checked"' if ext_enabled else ''}>{html.escape(ext_name)}</label></td>
            <td><label{style_remote}>{remote}</label></td>
            <td><label{style_branch}>{ext_branch}</label></td>
            <td><label{style_commit}>{commit_link}</label></td>
            <td><label{style_commit}>{date_link}</label></td>
        </tr>
"""

        code += """    </tbody>
</table>"""

    except Exception as e:
        print(f"[ERROR]: Config states {filepath}, {e}")
        code = f"""<!-- {time.time()} -->
<h2>Config Backup: {config_name}</h2>
<div><b>Filepath:</b> {filepath}</div>
<div><b>Created at:</b> {created_date}</div>
<h2>This file is corrupted</h2>"""

    return code
def extension_table():
    code = f"""<!-- {time.time()} -->
    <table id="extensions">
        <thead>
            <tr>
                <th>
                    <input class="gr-check-radio gr-checkbox all_extensions_toggle" type="checkbox" {'checked="checked"' if all(ext.enabled for ext in extensions.extensions) else ''} onchange="toggle_all_extensions(event)" />
                    <abbr title="Use checkbox to enable the extension; it will be enabled or disabled when you click apply button">Extension</abbr>
                </th>
                <th>URL</th>
                <th>Branch</th>
                <th>Version</th>
                <th>Date</th>
                <th><abbr title="Use checkbox to mark the extension for update; it will be updated when you click apply button">Update</abbr></th>
            </tr>
        </thead>
        <tbody>
    """

    for ext in extensions.extensions:
        ext: extensions.Extension
        ext.read_info_from_repo()

        remote = f"""<a href="{html.escape(ext.remote or '')}" target="_blank">{html.escape("built-in" if ext.is_builtin else ext.remote or '')}</a>"""

        if ext.can_update:
            ext_status = f"""<label><input class="gr-check-radio gr-checkbox" name="update_{html.escape(ext.name)}" checked="checked" type="checkbox">{html.escape(ext.status)}</label>"""
        else:
            ext_status = ext.status

        style = ""
        if shared.cmd_opts.disable_extra_extensions and not ext.is_builtin or shared.opts.disable_all_extensions == "extra" and not ext.is_builtin or shared.cmd_opts.disable_all_extensions or shared.opts.disable_all_extensions == "all":
            style = STYLE_PRIMARY

        version_link = ext.version
        if ext.commit_hash and ext.remote:
            version_link = make_commit_link(ext.commit_hash, ext.remote, ext.version)

        code += f"""
            <tr>
                <td><label{style}><input class="gr-check-radio gr-checkbox extension_toggle" name="enable_{html.escape(ext.name)}" type="checkbox" {'checked="checked"' if ext.enabled else ''} onchange="toggle_extension(event)" />{html.escape(ext.name)}</label></td>
                <td>{remote}</td>
                <td>{ext.branch}</td>
                <td>{version_link}</td>
                <td>{datetime.fromtimestamp(ext.commit_date) if ext.commit_date else ""}</td>
                <td{' class="extension_status"' if ext.remote is not None else ''}>{ext_status}</td>
            </tr>
    """

    code += """
        </tbody>
    </table>
    """

    return code
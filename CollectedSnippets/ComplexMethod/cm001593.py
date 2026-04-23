def refresh_available_extensions_from_data(selected_tags, showing_type, filtering_type, sort_column, filter_text=""):
    extlist = available_extensions["extensions"]
    installed_extensions = {extension.name for extension in extensions.extensions}
    installed_extension_urls = {normalize_git_url(extension.remote) for extension in extensions.extensions if extension.remote is not None}

    tags = available_extensions.get("tags", {})
    selected_tags = set(selected_tags)
    hidden = 0

    code = f"""<!-- {time.time()} -->
    <table id="available_extensions">
        <thead>
            <tr>
                <th>Extension</th>
                <th>Description</th>
                <th>Action</th>
            </tr>
        </thead>
        <tbody>
    """

    sort_reverse, sort_function = sort_ordering[sort_column if 0 <= sort_column < len(sort_ordering) else 0]

    for ext in sorted(extlist, key=sort_function, reverse=sort_reverse):
        name = ext.get("name", "noname")
        stars = int(ext.get("stars", 0))
        added = ext.get('added', 'unknown')
        update_time = get_date(ext, 'commit_time')
        create_time = get_date(ext, 'created_at')
        url = ext.get("url", None)
        description = ext.get("description", "")
        extension_tags = ext.get("tags", [])

        if url is None:
            continue

        existing = get_extension_dirname_from_url(url) in installed_extensions or normalize_git_url(url) in installed_extension_urls
        extension_tags = extension_tags + ["installed"] if existing else extension_tags

        if len(selected_tags) > 0:
            matched_tags = [x for x in extension_tags if x in selected_tags]
            if filtering_type == 'or':
                need_hide = len(matched_tags) > 0
            else:
                need_hide = len(matched_tags) == len(selected_tags)

            if showing_type == 'show':
                need_hide = not need_hide

            if need_hide:
                hidden += 1
                continue

        if filter_text and filter_text.strip():
            if filter_text.lower() not in html.escape(name).lower() and filter_text.lower() not in html.escape(description).lower():
                hidden += 1
                continue

        install_code = f"""<button onclick="install_extension_from_index(this, '{html.escape(url)}')" {"disabled=disabled" if existing else ""} class="lg secondary gradio-button custom-button">{"Install" if not existing else "Installed"}</button>"""

        tags_text = ", ".join([f"<span class='extension-tag' title='{tags.get(x, '')}'>{x}</span>" for x in extension_tags])

        code += f"""
            <tr>
                <td><a href="{html.escape(url)}" target="_blank">{html.escape(name)}</a><br />{tags_text}</td>
                <td>{html.escape(description)}<p class="info">
                <span class="date_added">Update: {html.escape(update_time)}  Added: {html.escape(added)}  Created: {html.escape(create_time)}</span><span class="star_count">stars: <b>{stars}</b></a></p></td>
                <td>{install_code}</td>
            </tr>

        """

        for tag in [x for x in extension_tags if x not in tags]:
            tags[tag] = tag

    code += """
        </tbody>
    </table>
    """

    if hidden > 0:
        code += f"<p>Extension hidden: {hidden}</p>"

    return code, list(tags)
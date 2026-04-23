def create_ui():
    import modules.ui

    config_states.list_config_states()

    threading.Thread(target=preload_extensions_git_metadata).start()

    with gr.Blocks(analytics_enabled=False) as ui:
        with gr.Tabs(elem_id="tabs_extensions"):
            with gr.TabItem("Installed", id="installed"):

                with gr.Row(elem_id="extensions_installed_top"):
                    apply_label = ("Apply and restart UI" if restart.is_restartable() else "Apply and quit")
                    apply = gr.Button(value=apply_label, variant="primary")
                    check = gr.Button(value="Check for updates")
                    extensions_disable_all = gr.Radio(label="Disable all extensions", choices=["none", "extra", "all"], value=shared.opts.disable_all_extensions, elem_id="extensions_disable_all")
                    extensions_disabled_list = gr.Text(elem_id="extensions_disabled_list", visible=False, container=False)
                    extensions_update_list = gr.Text(elem_id="extensions_update_list", visible=False, container=False)
                    refresh = gr.Button(value='Refresh', variant="compact")

                html = ""

                if shared.cmd_opts.disable_all_extensions or shared.cmd_opts.disable_extra_extensions or shared.opts.disable_all_extensions != "none":
                    if shared.cmd_opts.disable_all_extensions:
                        msg = '"--disable-all-extensions" was used, remove it to load all extensions again'
                    elif shared.opts.disable_all_extensions != "none":
                        msg = '"Disable all extensions" was set, change it to "none" to load all extensions again'
                    elif shared.cmd_opts.disable_extra_extensions:
                        msg = '"--disable-extra-extensions" was used, remove it to load all extensions again'
                    html = f'<span style="color: var(--primary-400);">{msg}</span>'

                with gr.Row():
                    info = gr.HTML(html)

                with gr.Row(elem_classes="progress-container"):
                    extensions_table = gr.HTML('Loading...', elem_id="extensions_installed_html")

                ui.load(fn=extension_table, inputs=[], outputs=[extensions_table], show_progress=False)
                refresh.click(fn=extension_table, inputs=[], outputs=[extensions_table], show_progress=False)

                apply.click(
                    fn=apply_and_restart,
                    _js="extensions_apply",
                    inputs=[extensions_disabled_list, extensions_update_list, extensions_disable_all],
                    outputs=[],
                )

                check.click(
                    fn=wrap_gradio_gpu_call(check_updates, extra_outputs=[gr.update()]),
                    _js="extensions_check",
                    inputs=[info, extensions_disabled_list],
                    outputs=[extensions_table, info],
                )

            with gr.TabItem("Available", id="available"):
                with gr.Row():
                    refresh_available_extensions_button = gr.Button(value="Load from:", variant="primary")
                    extensions_index_url = os.environ.get('WEBUI_EXTENSIONS_INDEX', "https://raw.githubusercontent.com/AUTOMATIC1111/stable-diffusion-webui-extensions/master/index.json")
                    available_extensions_index = gr.Text(value=extensions_index_url, label="Extension index URL", container=False)
                    extension_to_install = gr.Text(elem_id="extension_to_install", visible=False)
                    install_extension_button = gr.Button(elem_id="install_extension_button", visible=False)

                with gr.Row():
                    selected_tags = gr.CheckboxGroup(value=["ads", "localization", "installed"], label="Extension tags", choices=["script", "ads", "localization", "installed"], elem_classes=['compact-checkbox-group'])
                    sort_column = gr.Radio(value="newest first", label="Order", choices=["newest first", "oldest first", "a-z", "z-a", "internal order",'update time', 'create time', "stars"], type="index", elem_classes=['compact-checkbox-group'])

                with gr.Row():
                    showing_type = gr.Radio(value="hide", label="Showing type", choices=["hide", "show"], elem_classes=['compact-checkbox-group'])
                    filtering_type = gr.Radio(value="or", label="Filtering type", choices=["or", "and"], elem_classes=['compact-checkbox-group'])

                with gr.Row():
                    search_extensions_text = gr.Text(label="Search", container=False)

                install_result = gr.HTML()
                available_extensions_table = gr.HTML()

                refresh_available_extensions_button.click(
                    fn=modules.ui.wrap_gradio_call(refresh_available_extensions, extra_outputs=[gr.update(), gr.update(), gr.update(), gr.update()]),
                    inputs=[available_extensions_index, selected_tags, showing_type, filtering_type, sort_column],
                    outputs=[available_extensions_index, available_extensions_table, selected_tags, search_extensions_text, install_result],
                )

                install_extension_button.click(
                    fn=modules.ui.wrap_gradio_call_no_job(install_extension_from_index, extra_outputs=[gr.update(), gr.update()]),
                    inputs=[extension_to_install, selected_tags, showing_type, filtering_type, sort_column, search_extensions_text],
                    outputs=[available_extensions_table, extensions_table, install_result],
                )

                search_extensions_text.change(
                    fn=modules.ui.wrap_gradio_call_no_job(search_extensions, extra_outputs=[gr.update()]),
                    inputs=[search_extensions_text, selected_tags, showing_type, filtering_type, sort_column],
                    outputs=[available_extensions_table, install_result],
                )

                selected_tags.change(
                    fn=modules.ui.wrap_gradio_call_no_job(refresh_available_extensions_for_tags, extra_outputs=[gr.update()]),
                    inputs=[selected_tags, showing_type, filtering_type, sort_column, search_extensions_text],
                    outputs=[available_extensions_table, install_result]
                )

                showing_type.change(
                    fn=modules.ui.wrap_gradio_call_no_job(refresh_available_extensions_for_tags, extra_outputs=[gr.update()]),
                    inputs=[selected_tags, showing_type, filtering_type, sort_column, search_extensions_text],
                    outputs=[available_extensions_table, install_result]
                )

                filtering_type.change(
                    fn=modules.ui.wrap_gradio_call_no_job(refresh_available_extensions_for_tags, extra_outputs=[gr.update()]),
                    inputs=[selected_tags, showing_type, filtering_type, sort_column, search_extensions_text],
                    outputs=[available_extensions_table, install_result]
                )

                sort_column.change(
                    fn=modules.ui.wrap_gradio_call_no_job(refresh_available_extensions_for_tags, extra_outputs=[gr.update()]),
                    inputs=[selected_tags, showing_type, filtering_type, sort_column, search_extensions_text],
                    outputs=[available_extensions_table, install_result]
                )

            with gr.TabItem("Install from URL", id="install_from_url"):
                install_url = gr.Text(label="URL for extension's git repository")
                install_branch = gr.Text(label="Specific branch name", placeholder="Leave empty for default main branch")
                install_dirname = gr.Text(label="Local directory name", placeholder="Leave empty for auto")
                install_button = gr.Button(value="Install", variant="primary")
                install_result = gr.HTML(elem_id="extension_install_result")

                install_button.click(
                    fn=modules.ui.wrap_gradio_call_no_job(lambda *args: [gr.update(), *install_extension_from_url(*args)], extra_outputs=[gr.update(), gr.update()]),
                    inputs=[install_dirname, install_url, install_branch],
                    outputs=[install_url, extensions_table, install_result],
                )

            with gr.TabItem("Backup/Restore"):
                with gr.Row(elem_id="extensions_backup_top_row"):
                    config_states_list = gr.Dropdown(label="Saved Configs", elem_id="extension_backup_saved_configs", value="Current", choices=["Current"] + list(config_states.all_config_states.keys()))
                    modules.ui.create_refresh_button(config_states_list, config_states.list_config_states, lambda: {"choices": ["Current"] + list(config_states.all_config_states.keys())}, "refresh_config_states")
                    config_restore_type = gr.Radio(label="State to restore", choices=["extensions", "webui", "both"], value="extensions", elem_id="extension_backup_restore_type")
                    config_restore_button = gr.Button(value="Restore Selected Config", variant="primary", elem_id="extension_backup_restore")
                with gr.Row(elem_id="extensions_backup_top_row2"):
                    config_save_name = gr.Textbox("", placeholder="Config Name", show_label=False)
                    config_save_button = gr.Button(value="Save Current Config")

                config_states_info = gr.HTML("")
                config_states_table = gr.HTML("Loading...")
                ui.load(fn=update_config_states_table, inputs=[config_states_list], outputs=[config_states_table])

                config_save_button.click(fn=save_config_state, inputs=[config_save_name], outputs=[config_states_list, config_states_info])

                dummy_component = gr.Label(visible=False)
                config_restore_button.click(fn=restore_config_state, _js="config_state_confirm_restore", inputs=[dummy_component, config_states_list, config_restore_type], outputs=[config_states_info])

                config_states_list.change(
                    fn=update_config_states_table,
                    inputs=[config_states_list],
                    outputs=[config_states_table],
                )


    return ui
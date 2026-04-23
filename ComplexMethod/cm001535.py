def create_ui(self, loadsave, dummy_component):
        self.components = []
        self.component_dict = {}
        self.dummy_component = dummy_component

        shared.settings_components = self.component_dict

        # we add this as late as possible so that scripts have already registered their callbacks
        opts.data_labels.update(options_section(('callbacks', "Callbacks", "system"), {
            **shared_items.callbacks_order_settings(),
        }))

        opts.reorder()

        with gr.Blocks(analytics_enabled=False) as settings_interface:
            with gr.Row():
                with gr.Column(scale=6):
                    self.submit = gr.Button(value="Apply settings", variant='primary', elem_id="settings_submit")
                with gr.Column():
                    restart_gradio = gr.Button(value='Reload UI', variant='primary', elem_id="settings_restart_gradio")

            self.result = gr.HTML(elem_id="settings_result")

            self.quicksettings_names = opts.quicksettings_list
            self.quicksettings_names = {x: i for i, x in enumerate(self.quicksettings_names) if x != 'quicksettings'}

            self.quicksettings_list = []

            previous_section = None
            current_tab = None
            current_row = None
            with gr.Tabs(elem_id="settings"):
                for i, (k, item) in enumerate(opts.data_labels.items()):
                    section_must_be_skipped = item.section[0] is None

                    if previous_section != item.section and not section_must_be_skipped:
                        elem_id, text = item.section

                        if current_tab is not None:
                            current_row.__exit__()
                            current_tab.__exit__()

                        gr.Group()
                        current_tab = gr.TabItem(elem_id=f"settings_{elem_id}", label=text)
                        current_tab.__enter__()
                        current_row = gr.Column(elem_id=f"column_settings_{elem_id}", variant='compact')
                        current_row.__enter__()

                        previous_section = item.section

                    if k in self.quicksettings_names and not shared.cmd_opts.freeze_settings:
                        self.quicksettings_list.append((i, k, item))
                        self.components.append(dummy_component)
                    elif section_must_be_skipped:
                        self.components.append(dummy_component)
                    else:
                        component = create_setting_component(k)
                        self.component_dict[k] = component
                        self.components.append(component)

                if current_tab is not None:
                    current_row.__exit__()
                    current_tab.__exit__()

                with gr.TabItem("Defaults", id="defaults", elem_id="settings_tab_defaults"):
                    loadsave.create_ui()

                with gr.TabItem("Sysinfo", id="sysinfo", elem_id="settings_tab_sysinfo"):
                    gr.HTML('<a href="./internal/sysinfo-download" class="sysinfo_big_link" download>Download system info</a><br /><a href="./internal/sysinfo" target="_blank">(or open as text in a new page)</a>', elem_id="sysinfo_download")

                    with gr.Row():
                        with gr.Column(scale=1):
                            sysinfo_check_file = gr.File(label="Check system info for validity", type='binary')
                        with gr.Column(scale=1):
                            sysinfo_check_output = gr.HTML("", elem_id="sysinfo_validity")
                        with gr.Column(scale=100):
                            pass

                with gr.TabItem("Actions", id="actions", elem_id="settings_tab_actions"):
                    request_notifications = gr.Button(value='Request browser notifications', elem_id="request_notifications")
                    download_localization = gr.Button(value='Download localization template', elem_id="download_localization")
                    reload_script_bodies = gr.Button(value='Reload custom script bodies (No ui updates, No restart)', variant='secondary', elem_id="settings_reload_script_bodies")
                    with gr.Row():
                        unload_sd_model = gr.Button(value='Unload SD checkpoint to RAM', elem_id="sett_unload_sd_model")
                        reload_sd_model = gr.Button(value='Load SD checkpoint to VRAM from RAM', elem_id="sett_reload_sd_model")
                    with gr.Row():
                        calculate_all_checkpoint_hash = gr.Button(value='Calculate hash for all checkpoint', elem_id="calculate_all_checkpoint_hash")
                        calculate_all_checkpoint_hash_threads = gr.Number(value=1, label="Number of parallel calculations", elem_id="calculate_all_checkpoint_hash_threads", precision=0, minimum=1)

                with gr.TabItem("Licenses", id="licenses", elem_id="settings_tab_licenses"):
                    gr.HTML(shared.html("licenses.html"), elem_id="licenses")

                self.show_all_pages = gr.Button(value="Show all pages", elem_id="settings_show_all_pages")
                self.show_one_page = gr.Button(value="Show only one page", elem_id="settings_show_one_page", visible=False)
                self.show_one_page.click(lambda: None)

                self.search_input = gr.Textbox(value="", elem_id="settings_search", max_lines=1, placeholder="Search...", show_label=False)

                self.text_settings = gr.Textbox(elem_id="settings_json", value=lambda: opts.dumpjson(), visible=False)

            def call_func_and_return_text(func, text):
                def handler():
                    t = timer.Timer()
                    func()
                    t.record(text)

                    return f'{text} in {t.total:.1f}s'

                return handler

            unload_sd_model.click(
                fn=call_func_and_return_text(sd_models.unload_model_weights, 'Unloaded the checkpoint'),
                inputs=[],
                outputs=[self.result]
            )

            reload_sd_model.click(
                fn=call_func_and_return_text(lambda: sd_models.send_model_to_device(shared.sd_model), 'Loaded the checkpoint'),
                inputs=[],
                outputs=[self.result]
            )

            request_notifications.click(
                fn=lambda: None,
                inputs=[],
                outputs=[],
                _js='function(){}'
            )

            download_localization.click(
                fn=lambda: None,
                inputs=[],
                outputs=[],
                _js='download_localization'
            )

            def reload_scripts():
                scripts.reload_script_body_only()
                reload_javascript()  # need to refresh the html page

            reload_script_bodies.click(
                fn=reload_scripts,
                inputs=[],
                outputs=[]
            )

            restart_gradio.click(
                fn=shared.state.request_restart,
                _js='restart_reload',
                inputs=[],
                outputs=[],
            )

            def check_file(x):
                if x is None:
                    return ''

                if sysinfo.check(x.decode('utf8', errors='ignore')):
                    return 'Valid'

                return 'Invalid'

            sysinfo_check_file.change(
                fn=check_file,
                inputs=[sysinfo_check_file],
                outputs=[sysinfo_check_output],
            )

            def calculate_all_checkpoint_hash_fn(max_thread):
                checkpoints_list = sd_models.checkpoints_list.values()
                with ThreadPoolExecutor(max_workers=max_thread) as executor:
                    futures = [executor.submit(checkpoint.calculate_shorthash) for checkpoint in checkpoints_list]
                    completed = 0
                    for _ in as_completed(futures):
                        completed += 1
                        print(f"{completed} / {len(checkpoints_list)} ")
                    print("Finish calculating hash for all checkpoints")

            calculate_all_checkpoint_hash.click(
                fn=calculate_all_checkpoint_hash_fn,
                inputs=[calculate_all_checkpoint_hash_threads],
            )

        self.interface = settings_interface
def create_output_panel(tabname, outdir, toprow=None):
    res = OutputPanel()

    def open_folder(f, images=None, index=None):
        if shared.cmd_opts.hide_ui_dir_config:
            return

        try:
            if 'Sub' in shared.opts.open_dir_button_choice:
                image_dir = os.path.split(images[index]["name"].rsplit('?', 1)[0])[0]
                if 'temp' in shared.opts.open_dir_button_choice or not ui_tempdir.is_gradio_temp_path(image_dir):
                    f = image_dir
        except Exception:
            pass

        util.open_folder(f)

    with gr.Column(elem_id=f"{tabname}_results"):
        if toprow:
            toprow.create_inline_toprow_image()

        with gr.Column(variant='panel', elem_id=f"{tabname}_results_panel"):
            with gr.Group(elem_id=f"{tabname}_gallery_container"):
                res.gallery = gr.Gallery(label='Output', show_label=False, elem_id=f"{tabname}_gallery", columns=4, preview=True, height=shared.opts.gallery_height or None)

            with gr.Row(elem_id=f"image_buttons_{tabname}", elem_classes="image-buttons"):
                open_folder_button = ToolButton(folder_symbol, elem_id=f'{tabname}_open_folder', visible=not shared.cmd_opts.hide_ui_dir_config, tooltip="Open images output directory.")

                if tabname != "extras":
                    save = ToolButton('💾', elem_id=f'save_{tabname}', tooltip=f"Save the image to a dedicated directory ({shared.opts.outdir_save}).")
                    save_zip = ToolButton('🗃️', elem_id=f'save_zip_{tabname}', tooltip=f"Save zip archive with images to a dedicated directory ({shared.opts.outdir_save})")

                buttons = {
                    'img2img': ToolButton('🖼️', elem_id=f'{tabname}_send_to_img2img', tooltip="Send image and generation parameters to img2img tab."),
                    'inpaint': ToolButton('🎨️', elem_id=f'{tabname}_send_to_inpaint', tooltip="Send image and generation parameters to img2img inpaint tab."),
                    'extras': ToolButton('📐', elem_id=f'{tabname}_send_to_extras', tooltip="Send image and generation parameters to extras tab.")
                }

                if tabname == 'txt2img':
                    res.button_upscale = ToolButton('✨', elem_id=f'{tabname}_upscale', tooltip="Create an upscaled version of the current image using hires fix settings.")

            open_folder_button.click(
                fn=lambda images, index: open_folder(shared.opts.outdir_samples or outdir, images, index),
                _js="(y, w) => [y, selected_gallery_index()]",
                inputs=[
                    res.gallery,
                    open_folder_button,  # placeholder for index
                ],
                outputs=[],
            )

            if tabname != "extras":
                download_files = gr.File(None, file_count="multiple", interactive=False, show_label=False, visible=False, elem_id=f'download_files_{tabname}')

                with gr.Group():
                    res.infotext = gr.HTML(elem_id=f'html_info_{tabname}', elem_classes="infotext")
                    res.html_log = gr.HTML(elem_id=f'html_log_{tabname}', elem_classes="html-log")

                    res.generation_info = gr.Textbox(visible=False, elem_id=f'generation_info_{tabname}')
                    if tabname == 'txt2img' or tabname == 'img2img':
                        generation_info_button = gr.Button(visible=False, elem_id=f"{tabname}_generation_info_button")
                        generation_info_button.click(
                            fn=update_generation_info,
                            _js="function(x, y, z){ return [x, y, selected_gallery_index()] }",
                            inputs=[res.generation_info, res.infotext, res.infotext],
                            outputs=[res.infotext, res.infotext],
                            show_progress=False,
                        )

                    save.click(
                        fn=call_queue.wrap_gradio_call_no_job(save_files),
                        _js="(x, y, z, w) => [x, y, false, selected_gallery_index()]",
                        inputs=[
                            res.generation_info,
                            res.gallery,
                            res.infotext,
                            res.infotext,
                        ],
                        outputs=[
                            download_files,
                            res.html_log,
                        ],
                        show_progress=False,
                    )

                    save_zip.click(
                        fn=call_queue.wrap_gradio_call_no_job(save_files),
                        _js="(x, y, z, w) => [x, y, true, selected_gallery_index()]",
                        inputs=[
                            res.generation_info,
                            res.gallery,
                            res.infotext,
                            res.infotext,
                        ],
                        outputs=[
                            download_files,
                            res.html_log,
                        ]
                    )

            else:
                res.generation_info = gr.HTML(elem_id=f'html_info_x_{tabname}')
                res.infotext = gr.HTML(elem_id=f'html_info_{tabname}', elem_classes="infotext")
                res.html_log = gr.HTML(elem_id=f'html_log_{tabname}')

            paste_field_names = []
            if tabname == "txt2img":
                paste_field_names = modules.scripts.scripts_txt2img.paste_field_names
            elif tabname == "img2img":
                paste_field_names = modules.scripts.scripts_img2img.paste_field_names

            for paste_tabname, paste_button in buttons.items():
                parameters_copypaste.register_paste_params_button(parameters_copypaste.ParamBinding(
                    paste_button=paste_button, tabname=paste_tabname, source_tabname="txt2img" if tabname == "txt2img" else None, source_image_component=res.gallery,
                    paste_field_names=paste_field_names
                ))

    return res
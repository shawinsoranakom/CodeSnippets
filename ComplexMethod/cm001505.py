def connect_paste_params_buttons():
    for binding in registered_param_bindings:
        destination_image_component = paste_fields[binding.tabname]["init_img"]
        fields = paste_fields[binding.tabname]["fields"]
        override_settings_component = binding.override_settings_component or paste_fields[binding.tabname]["override_settings_component"]

        destination_width_component = next(iter([field for field, name in fields if name == "Size-1"] if fields else []), None)
        destination_height_component = next(iter([field for field, name in fields if name == "Size-2"] if fields else []), None)

        if binding.source_image_component and destination_image_component:
            need_send_dementions = destination_width_component and binding.tabname != 'inpaint'
            if isinstance(binding.source_image_component, gr.Gallery):
                func = send_image_and_dimensions if need_send_dementions else image_from_url_text
                jsfunc = "extract_image_from_gallery"
            else:
                func = send_image_and_dimensions if need_send_dementions else lambda x: x
                jsfunc = None

            binding.paste_button.click(
                fn=func,
                _js=jsfunc,
                inputs=[binding.source_image_component],
                outputs=[destination_image_component, destination_width_component, destination_height_component] if need_send_dementions else [destination_image_component],
                show_progress=False,
            )

        if binding.source_text_component is not None and fields is not None:
            connect_paste(binding.paste_button, fields, binding.source_text_component, override_settings_component, binding.tabname)

        if binding.source_tabname is not None and fields is not None:
            paste_field_names = ['Prompt', 'Negative prompt', 'Steps', 'Face restoration'] + (["Seed"] if shared.opts.send_seed else []) + binding.paste_field_names
            binding.paste_button.click(
                fn=lambda *x: x,
                inputs=[field for field, name in paste_fields[binding.source_tabname]["fields"] if name in paste_field_names],
                outputs=[field for field, name in fields if name in paste_field_names],
                show_progress=False,
            )

        binding.paste_button.click(
            fn=None,
            _js=f"switch_to_{binding.tabname}",
            inputs=None,
            outputs=None,
            show_progress=False,
        )
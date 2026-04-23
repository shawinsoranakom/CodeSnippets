def callbacks_order_settings():
    options = {
        "sd_vae_explanation": OptionHTML("""
    For categories below, callbacks added to dropdowns happen before others, in order listed.
    """),

    }

    callback_options = {}

    for category, _ in script_callbacks.enumerate_callbacks():
        callback_options[category] = script_callbacks.ordered_callbacks(category, enable_user_sort=False)

    for method_name in scripts.scripts_txt2img.callback_names:
        callback_options["script_" + method_name] = scripts.scripts_txt2img.create_ordered_callbacks_list(method_name, enable_user_sort=False)

    for method_name in scripts.scripts_img2img.callback_names:
        callbacks = callback_options.get("script_" + method_name, [])

        for addition in scripts.scripts_img2img.create_ordered_callbacks_list(method_name, enable_user_sort=False):
            if any(x.name == addition.name for x in callbacks):
                continue

            callbacks.append(addition)

        callback_options["script_" + method_name] = callbacks

    for category, callbacks in callback_options.items():
        if not callbacks:
            continue

        option_info = OptionInfo([], f"{category} callback priority", ui_components.DropdownMulti, {"choices": [x.name for x in callbacks]})
        option_info.needs_restart()
        option_info.html("<div class='info'>Default order: <ol>" + "".join(f"<li>{html.escape(x.name)}</li>\n" for x in callbacks) + "</ol></div>")
        options['prioritized_callbacks_' + category] = option_info

    return options
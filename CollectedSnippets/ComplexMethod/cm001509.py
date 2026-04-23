def paste_func(prompt):
        if not prompt and not shared.cmd_opts.hide_ui_dir_config and not shared.cmd_opts.no_prompt_history:
            filename = os.path.join(data_path, "params.txt")
            try:
                with open(filename, "r", encoding="utf8") as file:
                    prompt = file.read()
            except OSError:
                pass

        params = parse_generation_parameters(prompt)
        script_callbacks.infotext_pasted_callback(prompt, params)
        res = []

        for output, key in paste_fields:
            if callable(key):
                try:
                    v = key(params)
                except Exception:
                    errors.report(f"Error executing {key}", exc_info=True)
                    v = None
            else:
                v = params.get(key, None)

            if v is None:
                res.append(gr.update())
            elif isinstance(v, type_of_gr_update):
                res.append(v)
            else:
                try:
                    valtype = type(output.value)

                    if valtype == bool and v == "False":
                        val = False
                    elif valtype == int:
                        val = float(v)
                    else:
                        val = valtype(v)

                    res.append(gr.update(value=val))
                except Exception:
                    res.append(gr.update())

        return res
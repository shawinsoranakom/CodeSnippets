def create_setting_component(key, is_quicksettings=False):
    def fun():
        return opts.data[key] if key in opts.data else opts.data_labels[key].default

    info = opts.data_labels[key]
    t = type(info.default)

    args = info.component_args() if callable(info.component_args) else info.component_args

    if info.component is not None:
        comp = info.component
    elif t == str:
        comp = gr.Textbox
    elif t == int:
        comp = gr.Number
    elif t == bool:
        comp = gr.Checkbox
    else:
        raise Exception(f'bad options item type: {t} for key {key}')

    elem_id = f"setting_{key}"

    if info.refresh is not None:
        if is_quicksettings:
            res = comp(label=info.label, value=fun(), elem_id=elem_id, **(args or {}))
            ui_common.create_refresh_button(res, info.refresh, info.component_args, f"refresh_{key}")
        else:
            with FormRow():
                res = comp(label=info.label, value=fun(), elem_id=elem_id, **(args or {}))
                ui_common.create_refresh_button(res, info.refresh, info.component_args, f"refresh_{key}")
    else:
        res = comp(label=info.label, value=fun(), elem_id=elem_id, **(args or {}))

    return res
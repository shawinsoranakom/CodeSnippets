def b_delete_audio(*checkbox_list):
    global g_data_json, g_index, g_max_json_index
    b_save_file()
    change = False
    for i, checkbox in reversed(list(enumerate(checkbox_list))):
        if g_index + i < len(g_data_json):
            if checkbox == True:
                g_data_json.pop(g_index + i)
                change = True

    g_max_json_index = len(g_data_json) - 1
    if g_index > g_max_json_index:
        g_index = g_max_json_index
        g_index = g_index if g_index >= 0 else 0
    if change:
        b_save_file()
    # return gr.Slider(value=g_index, maximum=(g_max_json_index if g_max_json_index>=0 else 0)), *b_change_index(g_index, g_batch)
    return {
        "value": g_index,
        "__type__": "update",
        "maximum": (g_max_json_index if g_max_json_index >= 0 else 0),
    }, *b_change_index(g_index, g_batch)
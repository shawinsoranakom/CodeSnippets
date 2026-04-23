def read_avail_plugin_enum():
    from crazy_functional import get_crazy_functions
    plugin_arr = get_crazy_functions()
    # remove plugins with out explanation
    plugin_arr = {k:v for k, v in plugin_arr.items() if ('Info' in v) and ('Function' in v)}
    plugin_arr_info = {"F_{:04d}".format(i):v["Info"] for i, v in enumerate(plugin_arr.values(), start=1)}
    plugin_arr_dict = {"F_{:04d}".format(i):v for i, v in enumerate(plugin_arr.values(), start=1)}
    plugin_arr_dict_parse = {"F_{:04d}".format(i):v for i, v in enumerate(plugin_arr.values(), start=1)}
    plugin_arr_dict_parse.update({f"F_{i}":v for i, v in enumerate(plugin_arr.values(), start=1)})
    prompt = json.dumps(plugin_arr_info, ensure_ascii=False, indent=2)
    prompt = "\n\nThe definition of PluginEnum:\nPluginEnum=" + prompt
    return prompt, plugin_arr_dict, plugin_arr_dict_parse
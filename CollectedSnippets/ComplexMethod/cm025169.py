def dump_dict(layer, indent_count=3, listi=False, **kwargs):
    """Display a dict.

    A friendly version of print yaml_loader.yaml.dump(config).
    """

    def sort_dict_key(val):
        """Return the dict key for sorting."""
        key = str(val[0]).lower()
        return "0" if key == "platform" else key

    indent_str = indent_count * " "
    if listi or isinstance(layer, list):
        indent_str = indent_str[:-1] + "-"
    if isinstance(layer, Mapping):
        for key, value in sorted(layer.items(), key=sort_dict_key):
            if isinstance(value, (dict, list)):
                print(indent_str, str(key) + ":", line_info(value, **kwargs))
                dump_dict(value, indent_count + 2, **kwargs)
            else:
                print(indent_str, str(key) + ":", value, line_info(key, **kwargs))
            indent_str = indent_count * " "
    if isinstance(layer, Sequence):
        for i in layer:
            if isinstance(i, dict):
                dump_dict(i, indent_count + 2, True, **kwargs)
            else:
                print(" ", indent_str, i)
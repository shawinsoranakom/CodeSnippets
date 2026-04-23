def _format_url(url: str, path_params: dict) -> str:
    expected_path_param = re.findall(r"{(.*?)}", url)
    new_params = {}
    for param in expected_path_param:
        clean_param = param.lstrip(".;").rstrip("*")
        val = path_params[clean_param]
        if isinstance(val, list):
            if param[0] == ".":
                sep = "." if param[-1] == "*" else ","
                new_val = "." + sep.join(val)
            elif param[0] == ";":
                sep = f"{clean_param}=" if param[-1] == "*" else ","
                new_val = f"{clean_param}=" + sep.join(val)
            else:
                new_val = ",".join(val)
        elif isinstance(val, dict):
            kv_sep = "=" if param[-1] == "*" else ","
            kv_strs = [kv_sep.join((k, v)) for k, v in val.items()]
            if param[0] == ".":
                sep = "."
                new_val = "."
            elif param[0] == ";":
                sep = ";"
                new_val = ";"
            else:
                sep = ","
                new_val = ""
            new_val += sep.join(kv_strs)
        elif param[0] == ".":
            new_val = f".{val}"
        elif param[0] == ";":
            new_val = f";{clean_param}={val}"
        else:
            new_val = val
        new_params[param] = new_val
    return url.format(**new_params)
def _normalize_name(param_name: ParameterName, validate=False) -> ParameterName:
        if is_arn(param_name):
            resource_name = extract_resource_from_arn(param_name).replace("parameter/", "")
            # if the parameter name is only the root path we want to look up without the leading slash.
            # Otherwise, we add the leading slash
            if "/" in resource_name:
                resource_name = f"/{resource_name}"
            return resource_name

        if validate:
            if "//" in param_name or ("/" in param_name and not param_name.startswith("/")):
                raise InvalidParameterNameException()
        param_name = param_name.strip("/")
        param_name = param_name.replace("//", "/")
        if "/" in param_name:
            param_name = f"/{param_name}"
        return param_name
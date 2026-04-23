def collect_implemented_provider_operations(
    provider_module: str = "localstack.services",
    provider_module_regex: Pattern = re.compile(r".*\.provider[A-Za-z_0-9]*$"),
    provider_class_regex: Pattern = re.compile(r".*Provider$"),
    asf_api_module: str = "localstack.aws.api",
) -> list[tuple[type, type, str]]:
    """
    Collects all implemented operations on all provider classes together with their base classes (generated API classes).
    :param provider_module: module to start collecting in
    :param provider_module_regex: Regex to filter the module names for
    :param provider_class_regex: Regex to filter the provider class names for
    :param asf_api_module: module which contains the generated ASF APIs
    :return: list of tuple, where each tuple is (provider_class: type, base_class: type, provider_function: str)
    """
    results = []
    provider_classes = _collect_provider_classes(
        provider_module, provider_module_regex, provider_class_regex
    )
    for provider_class in provider_classes:
        for base_class in provider_class.__bases__:
            base_parent_module = ".".join(base_class.__module__.split(".")[:-1])
            if base_parent_module == asf_api_module:
                # find all functions on the provider class which are also defined in the super class and are not dunder functions
                provider_functions = [
                    method
                    for method in dir(provider_class)
                    if hasattr(base_class, method)
                    and isinstance(getattr(base_class, method), FunctionType)
                    and method.startswith("__") is False
                ]
                for provider_function in provider_functions:
                    results.append((provider_class, base_class, provider_function))
    return results
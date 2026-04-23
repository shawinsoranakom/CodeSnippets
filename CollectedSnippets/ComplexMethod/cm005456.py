def lazy_load_kernel(kernel_name: str, mapping: dict[str, ModuleType | None] = _KERNEL_MODULE_MAPPING):
    if kernel_name in mapping and isinstance(mapping[kernel_name], ModuleType):
        return mapping[kernel_name]
    if kernel_name not in _HUB_KERNEL_MAPPING:
        logger.warning_once(f"Kernel {kernel_name} not found in _HUB_KERNEL_MAPPING")
        mapping[kernel_name] = None
        return None
    if _kernels_available:
        try:
            repo_id = _HUB_KERNEL_MAPPING[kernel_name]["repo_id"]
            revision = _HUB_KERNEL_MAPPING[kernel_name].get("revision", None)
            version = _HUB_KERNEL_MAPPING[kernel_name].get("version", None)
            kernel = get_kernel(repo_id, revision=revision, version=version)
            mapping[kernel_name] = kernel
        except FileNotFoundError:
            mapping[kernel_name] = None
        except AssertionError:
            # Happens when torch is built without an accelerator backend; fall back to slow path.
            mapping[kernel_name] = None

    else:
        # Try to import is_{kernel_name}_available from ..utils
        import importlib

        new_kernel_name = kernel_name.replace("-", "_")
        func_name = f"is_{new_kernel_name}_available"

        try:
            utils_mod = importlib.import_module("..utils.import_utils", __package__)
            is_kernel_available = getattr(utils_mod, func_name, None)
        except Exception:
            is_kernel_available = None

        if callable(is_kernel_available) and is_kernel_available():
            # Try to import the module "{kernel_name}" from parent package level
            try:
                module = importlib.import_module(f"{new_kernel_name}")
                mapping[kernel_name] = module
                return module
            except Exception:
                mapping[kernel_name] = None
        else:
            mapping[kernel_name] = None

    return mapping[kernel_name]
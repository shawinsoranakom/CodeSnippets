def get_public_overridable_apis(pytorch_root="/raid/rzou/pt/debug-cpu"):
    results = {}
    all_overridable_apis = set(torch.overrides.get_testing_overrides().keys())
    for module, module_name, src in public_docs:
        with open(f"{pytorch_root}/{src}") as f:
            lines = f.readlines()
        # APIs either begin with 4 spaces or ".. autofunction::"
        api_lines1 = [line.strip() for line in lines if line.startswith(" " * 4)]
        api_lines2 = [
            line.strip()[len(".. autofunction:: ") :]
            for line in lines
            if line.startswith(".. autofunction::")
        ]
        lines = api_lines1 + api_lines2
        lines = [line.removeprefix("Tensor.") for line in lines]
        lines = [line for line in lines if hasattr(module, line)]
        for line in lines:
            api = getattr(module, line)
            if api in all_overridable_apis:
                results[f"{module_name}.{line}"] = api
    return results
def _re_import_modules():
    hf_hub_module_names = [k for k in sys.modules if k.startswith("huggingface_hub")]
    transformers_module_names = [
        k
        for k in sys.modules
        if k.startswith("transformers") and not k.startswith("transformers_modules")
    ]

    # These modules are aliased in Transformers v5 and so cannot be reloaded directly
    aliased_module_patterns = [
        r".+\.tokenization_utils$",
        r".+\.tokenization_utils_fast$",
        r".+\.image_processing_utils_fast$",
        r".+\.models\..+\.image_processing_.+_fast$",
    ]

    reload_exception = None
    for module_name in hf_hub_module_names + transformers_module_names:
        if any(re.match(pattern, module_name) for pattern in aliased_module_patterns):
            # Remove from sys.modules so they are re-aliased on next import
            del sys.modules[module_name]
            continue
        try:
            importlib.reload(sys.modules[module_name])
        except Exception as e:
            reload_exception = e
            # Try to continue clean up so that other tests are less likely to
            # be affected

    # Error this test if reloading a module failed
    if reload_exception is not None:
        raise reload_exception
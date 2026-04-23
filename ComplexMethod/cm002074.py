def tearDownClass(cls):
        for attr in [
            "model_kernelized",
            "model_not_kernelized",
            "tokenizer",
        ]:
            if hasattr(cls, attr):
                try:
                    delattr(cls, attr)
                except Exception as e:
                    print(f"Could not delete attribute {attr}: {e}")

        # Clear any temporary kernel module cache entries populated by tests
        try:
            keys_to_remove = [
                k for k, v in list(_KERNEL_MODULE_MAPPING.items()) if v is None or isinstance(v, types.ModuleType)
            ]
            for k in keys_to_remove:
                _KERNEL_MODULE_MAPPING.pop(k, None)
        except Exception as e:
            print(f"Could not clear kernel module cache: {e}")
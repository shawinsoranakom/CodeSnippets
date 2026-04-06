def get_test_main_mod(mod_path: str) -> ModuleType:
    test_main_mod = importlib.import_module(f"{mod_path}.test_main")
    return test_main_mod
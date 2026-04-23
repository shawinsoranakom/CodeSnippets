def get_main_mod(mod_path: str) -> ModuleType:
    main_mod = importlib.import_module(f"{mod_path}.main")
    return main_mod
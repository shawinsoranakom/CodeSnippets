def load_upscalers():
    # We can only do this 'magic' method to dynamically load upscalers if they are referenced,
    # so we'll try to import any _model.py files before looking in __subclasses__
    modules_dir = os.path.join(shared.script_path, "modules")
    for file in os.listdir(modules_dir):
        if "_model.py" in file:
            model_name = file.replace("_model.py", "")
            full_model = f"modules.{model_name}_model"
            try:
                importlib.import_module(full_model)
            except Exception:
                pass

    data = []
    commandline_options = vars(shared.cmd_opts)

    # some of upscaler classes will not go away after reloading their modules, and we'll end
    # up with two copies of those classes. The newest copy will always be the last in the list,
    # so we go from end to beginning and ignore duplicates
    used_classes = {}
    for cls in reversed(Upscaler.__subclasses__()):
        classname = str(cls)
        if classname not in used_classes:
            used_classes[classname] = cls

    for cls in reversed(used_classes.values()):
        name = cls.__name__
        cmd_name = f"{name.lower().replace('upscaler', '')}_models_path"
        commandline_model_path = commandline_options.get(cmd_name, None)
        scaler = cls(commandline_model_path)
        scaler.user_path = commandline_model_path
        scaler.model_download_path = commandline_model_path or scaler.model_path
        data += scaler.scalers

    shared.sd_upscalers = sorted(
        data,
        # Special case for UpscalerNone keeps it at the beginning of the list.
        key=lambda x: x.name.lower() if not isinstance(x.scaler, (UpscalerNone, UpscalerLanczos, UpscalerNearest)) else ""
    )
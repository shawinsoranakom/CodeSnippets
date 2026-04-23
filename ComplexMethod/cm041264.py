def create_lambda_archive(
    script: str,
    get_content: bool = False,
    libs: list[str] = None,
    runtime: str = None,
    file_name: str = None,
    exclude_func: Callable[[str], bool] = None,
):
    """Utility method to create a Lambda function archive"""
    if libs is None:
        libs = []
    runtime = runtime or LAMBDA_DEFAULT_RUNTIME

    with tempfile.TemporaryDirectory(prefix=ARCHIVE_DIR_PREFIX) as tmp_dir:
        file_name = file_name or get_handler_file_from_name(LAMBDA_DEFAULT_HANDLER, runtime=runtime)
        script_file = os.path.join(tmp_dir, file_name)
        if os.path.sep in script_file:
            mkdir(os.path.dirname(script_file))
            # create __init__.py files along the path to allow Python imports
            path = file_name.split(os.path.sep)
            for i in range(1, len(path)):
                save_file(os.path.join(tmp_dir, *(path[:i] + ["__init__.py"])), "")
        save_file(script_file, script)
        chmod_r(script_file, 0o777)
        # copy libs
        for lib in libs:
            paths = [lib, f"{lib}.py"]
            try:
                module = importlib.import_module(lib)
                paths.append(module.__file__)
            except Exception:
                pass
            target_dir = tmp_dir
            root_folder = os.path.join(LOCALSTACK_VENV_FOLDER, "lib/python*/site-packages")
            if lib == "localstack":
                paths = ["localstack/*.py", "localstack/utils"]
                root_folder = LOCALSTACK_ROOT_FOLDER
                target_dir = os.path.join(tmp_dir, lib)
                mkdir(target_dir)
            for path in paths:
                file_to_copy = path if path.startswith("/") else os.path.join(root_folder, path)
                for file_path in glob.glob(file_to_copy):
                    name = os.path.join(target_dir, file_path.split(os.path.sep)[-1])
                    if os.path.isdir(file_path):
                        cp_r(file_path, name)
                    else:
                        shutil.copyfile(file_path, name)

        if exclude_func:
            for dirpath, folders, files in os.walk(tmp_dir):
                for name in list(folders) + list(files):
                    full_name = os.path.join(dirpath, name)
                    relative = os.path.relpath(full_name, start=tmp_dir)
                    if exclude_func(relative):
                        rm_rf(full_name)

        # create zip file
        result = create_zip_file(tmp_dir, get_content=get_content)
        return result
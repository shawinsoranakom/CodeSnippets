def create_legacy_directory(package_dir):
    src_dir = os.path.join(package_dir, "src")
    # Make keras/_tf_keras/ by copying keras/
    tf_keras_dirpath_parent = os.path.join(package_dir, "_tf_keras")
    tf_keras_dirpath = os.path.join(tf_keras_dirpath_parent, "keras")
    os.makedirs(tf_keras_dirpath, exist_ok=True)
    with open(os.path.join(tf_keras_dirpath_parent, "__init__.py"), "w") as f:
        f.write("from keras._tf_keras import keras\n")
    with open(os.path.join(package_dir, "__init__.py")) as f:
        init_file = f.read()
        init_file = init_file.replace(
            "from keras import _legacy as _legacy",
            "from keras import _tf_keras as _tf_keras",
        )
    with open(os.path.join(package_dir, "__init__.py"), "w") as f:
        f.write(init_file)
    # Remove the import of `_tf_keras` in `keras/_tf_keras/keras/__init__.py`
    init_file = init_file.replace("from keras import _tf_keras\n", "\n")
    with open(os.path.join(tf_keras_dirpath, "__init__.py"), "w") as f:
        f.write(init_file)
    for dirname in os.listdir(package_dir):
        dirpath = os.path.join(package_dir, dirname)
        if os.path.isdir(dirpath) and dirname not in (
            "_legacy",
            "_tf_keras",
            "src",
        ):
            destpath = os.path.join(tf_keras_dirpath, dirname)
            if os.path.exists(destpath):
                shutil.rmtree(destpath)
            shutil.copytree(
                dirpath,
                destpath,
                ignore=ignore_files,
            )

    # Copy keras/_legacy/ file contents to keras/_tf_keras/keras
    legacy_submodules = [
        path[:-3]
        for path in os.listdir(os.path.join(src_dir, "legacy"))
        if path.endswith(".py")
    ]
    legacy_submodules += [
        path
        for path in os.listdir(os.path.join(src_dir, "legacy"))
        if os.path.isdir(os.path.join(src_dir, "legacy", path))
    ]
    for root, _, fnames in os.walk(os.path.join(package_dir, "_legacy")):
        for fname in fnames:
            if fname.endswith(".py"):
                legacy_fpath = os.path.join(root, fname)
                tf_keras_root = root.replace(
                    os.path.join(os.path.sep, "_legacy"),
                    os.path.join(os.path.sep, "_tf_keras", "keras"),
                )
                core_api_fpath = os.path.join(
                    root.replace(os.path.join(os.path.sep, "_legacy"), ""),
                    fname,
                )
                if not os.path.exists(tf_keras_root):
                    os.makedirs(tf_keras_root)
                tf_keras_fpath = os.path.join(tf_keras_root, fname)
                with open(legacy_fpath) as f:
                    legacy_contents = f.read()
                    legacy_contents = legacy_contents.replace(
                        "keras._legacy", "keras._tf_keras.keras"
                    )
                if os.path.exists(core_api_fpath):
                    with open(core_api_fpath) as f:
                        core_api_contents = f.read()
                    core_api_contents = core_api_contents.replace(
                        "from keras import _tf_keras as _tf_keras\n", ""
                    )
                    for legacy_submodule in legacy_submodules:
                        core_api_contents = core_api_contents.replace(
                            f"from keras import {legacy_submodule} as {legacy_submodule}\n",  # noqa: E501
                            "",
                        )
                        core_api_contents = core_api_contents.replace(
                            f"keras.{legacy_submodule}",
                            f"keras._tf_keras.keras.{legacy_submodule}",
                        )
                    # Remove duplicate generated comments string.
                    legacy_contents = re.sub(r"\n", r"\\n", legacy_contents)
                    legacy_contents = re.sub('""".*"""', "", legacy_contents)
                    legacy_contents = re.sub(r"\\n", r"\n", legacy_contents)
                    # If the same module is in legacy and core_api, use legacy
                    legacy_imports = re.findall(
                        r"import (\w+)", legacy_contents
                    )
                    for import_name in legacy_imports:
                        core_api_contents = re.sub(
                            f"\n.* import {import_name} as {import_name}\n",
                            r"\n",
                            core_api_contents,
                        )
                    legacy_contents = f"{core_api_contents}\n{legacy_contents}"
                with open(tf_keras_fpath, "w") as f:
                    f.write(legacy_contents)

    # Delete keras/api/_legacy/
    shutil.rmtree(os.path.join(package_dir, "_legacy"))
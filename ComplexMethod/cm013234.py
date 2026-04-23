def install_cpp_extension(extension_root):
    # Wipe the build / install dirs if they exist
    build_dir = os.path.join(extension_root, "build")
    install_dir = os.path.join(extension_root, "install")
    for d in (build_dir, install_dir):
        if os.path.exists(d):
            shutil.rmtree(d)

    # Build the extension
    cmd = [sys.executable, "-m", "pip", "install", extension_root, "-v", "--no-build-isolation", "--root", install_dir]
    return_code = shell(cmd, cwd=extension_root, env=os.environ)
    if return_code != 0:
        raise RuntimeError(f"build failed for cpp extension at {extension_root}")

    mod_install_dir = None
    # install directory is the one that is named site-packages
    for root, directories, _ in os.walk(install_dir):
        for directory in directories:
            if "-packages" in directory:
                mod_install_dir = os.path.join(root, directory)

    if mod_install_dir is None:
        raise RuntimeError(f"installation failed for cpp extension at {extension_root}")

    if mod_install_dir not in sys.path:
        sys.path.insert(0, mod_install_dir)
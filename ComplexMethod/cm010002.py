def check_mac_wheel_minos() -> None:
    if sys.platform != "darwin":
        return

    wheel_dir = os.getenv("PYTORCH_FINAL_PACKAGE_DIR", "")

    if wheel_dir and os.path.isdir(wheel_dir):
        # Mode 1: extract dylibs from .whl file
        whls = list(Path(wheel_dir).glob("*.whl"))
        if not whls:
            print(f"No .whl files in {wheel_dir}, skipping wheel minos check")
            return

        macos_whl_re = re.compile(r"macosx_(\d+)_(\d+)_(\w+)\.whl$")
        for whl in whls:
            print(f"Checking wheel tag minos for: {whl.name}")
            m = macos_whl_re.search(whl.name)
            if not m:
                print(f"No macOS platform tag in {whl.name}, skipping")
                continue
            expected_minos = f"{m.group(1)}.{m.group(2)}"

            with tempfile.TemporaryDirectory() as tmpdir:
                with zipfile.ZipFile(whl, "r") as zf:
                    dylib_names = [n for n in zf.namelist() if n.endswith(".dylib")]
                    if not dylib_names:
                        print("No .dylib files in wheel, skipping minos check")
                        continue
                    for name in dylib_names:
                        zf.extract(name, tmpdir)
                dylibs = list(Path(tmpdir).rglob("*.dylib"))
                _check_dylibs_minos(dylibs, expected_minos, whl.name)
    else:
        # Mode 2: read from installed torch package
        print("PYTORCH_FINAL_PACKAGE_DIR not set, checking installed torch dylibs")
        try:
            tags = _extract_installed_wheel_tags("torch")
        except Exception as e:
            print(f"Could not read installed torch metadata: {e}, skipping")
            return

        expected_minos = None
        for tag_str in tags:
            m = re.search(r"macosx_(\d+)_(\d+)_\w+", tag_str)
            if m:
                expected_minos = f"{m.group(1)}.{m.group(2)}"
                break

        if not expected_minos:
            print("No macOS platform tag found in installed torch metadata, skipping")
            return

        print(f"Expected minos from installed wheel tag: {expected_minos}")

        import torch

        torch_dir = Path(torch.__file__).parent
        dylibs = list(torch_dir.rglob("*.dylib"))
        if not dylibs:
            raise RuntimeError("No .dylib files found in installed torch")
        _check_dylibs_minos(dylibs, expected_minos, "installed torch")
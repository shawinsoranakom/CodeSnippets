def generate_source_files(ns):
    if ns.zip_lib:
        zip_name = PYTHON_ZIP_NAME
        zip_path = ns.temp / zip_name
        if zip_path.is_file():
            zip_path.unlink()
        elif zip_path.is_dir():
            log_error(
                "Cannot create zip file because a directory exists by the same name"
            )
            return
        log_info("Generating {} in {}", zip_name, ns.temp)
        ns.temp.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for dest, src in get_lib_layout(ns):
                _write_to_zip(zf, dest, src, ns, checked=False)

    if ns.include_underpth:
        log_info("Generating {} in {}", PYTHON_PTH_NAME, ns.temp)
        ns.temp.mkdir(parents=True, exist_ok=True)
        with open(ns.temp / PYTHON_PTH_NAME, "w", encoding="utf-8") as f:
            if ns.zip_lib:
                print(PYTHON_ZIP_NAME, file=f)
                if ns.include_pip:
                    print("packages", file=f)
            else:
                print("Lib", file=f)
                print("Lib/site-packages", file=f)
            if not ns.flat_dlls:
                print("DLLs", file=f)
            print(".", file=f)
            print(file=f)
            print("# Uncomment to run site.main() automatically", file=f)
            print("#import site", file=f)

    if ns.include_pip:
        log_info("Extracting pip")
        extract_pip_files(ns)

    if ns.include_install_json:
        log_info("Generating __install__.json in {}", ns.temp)
        ns.temp.mkdir(parents=True, exist_ok=True)
        with open(ns.temp / "__install__.json", "w", encoding="utf-8") as f:
            json.dump(calculate_install_json(ns), f, indent=2)
    elif ns.include_install_embed_json:
        log_info("Generating embeddable __install__.json in {}", ns.temp)
        ns.temp.mkdir(parents=True, exist_ok=True)
        with open(ns.temp / "__install__.json", "w", encoding="utf-8") as f:
            json.dump(calculate_install_json(ns, for_embed=True), f, indent=2)
    elif ns.include_install_test_json:
        log_info("Generating test __install__.json in {}", ns.temp)
        ns.temp.mkdir(parents=True, exist_ok=True)
        with open(ns.temp / "__install__.json", "w", encoding="utf-8") as f:
            json.dump(calculate_install_json(ns, for_test=True), f, indent=2)
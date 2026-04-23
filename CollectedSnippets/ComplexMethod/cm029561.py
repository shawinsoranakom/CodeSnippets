def copy_files(files, ns):
    if ns.copy:
        ns.copy.mkdir(parents=True, exist_ok=True)

    try:
        total = len(files)
    except TypeError:
        total = None
    count = 0

    zip_file = _create_zip_file(ns)
    try:
        need_compile = []
        in_catalog = []

        for dest, src in files:
            count += 1
            if count % 10 == 0:
                if total:
                    log_info("Processed {:>4} of {} files", count, total)
                else:
                    log_info("Processed {} files", count)
            log_debug("Processing {!s}", src)

            if isinstance(src, tuple):
                src, content = src
                if ns.copy:
                    log_debug("Copy {} -> {}", src, ns.copy / dest)
                    (ns.copy / dest).parent.mkdir(parents=True, exist_ok=True)
                    with open(ns.copy / dest, "wb") as f:
                        f.write(content)
                if ns.zip:
                    log_debug("Zip {} into {}", src, ns.zip)
                    zip_file.writestr(str(dest), content)
                continue

            if (
                ns.precompile
                and src in PY_FILES
                and src not in EXCLUDE_FROM_COMPILE
                and src.parent not in DATA_DIRS
                and os.path.normcase(str(dest)).startswith(os.path.normcase("Lib"))
            ):
                if ns.copy:
                    need_compile.append((dest, ns.copy / dest))
                else:
                    (ns.temp / "Lib" / dest).parent.mkdir(parents=True, exist_ok=True)
                    copy_if_modified(src, ns.temp / "Lib" / dest)
                    need_compile.append((dest, ns.temp / "Lib" / dest))

            if src not in EXCLUDE_FROM_CATALOG:
                in_catalog.append((src.name, src))

            if ns.copy:
                log_debug("Copy {} -> {}", src, ns.copy / dest)
                (ns.copy / dest).parent.mkdir(parents=True, exist_ok=True)
                try:
                    copy_if_modified(src, ns.copy / dest)
                except shutil.SameFileError:
                    pass

            if ns.zip:
                log_debug("Zip {} into {}", src, ns.zip)
                zip_file.write(src, str(dest))

        if need_compile:
            for dest, src in need_compile:
                compiled = [
                    _compile_one_py(src, None, dest, optimize=0),
                    _compile_one_py(src, None, dest, optimize=1),
                    _compile_one_py(src, None, dest, optimize=2),
                ]
                for c in compiled:
                    if not c:
                        continue
                    cdest = Path(dest).parent / Path(c).relative_to(src.parent)
                    if ns.zip:
                        log_debug("Zip {} into {}", c, ns.zip)
                        zip_file.write(c, str(cdest))
                    in_catalog.append((cdest.name, cdest))

        if ns.catalog:
            # Just write out the CDF now. Compilation and signing is
            # an extra step
            log_info("Generating {}", ns.catalog)
            ns.catalog.parent.mkdir(parents=True, exist_ok=True)
            write_catalog(ns.catalog, in_catalog)

    finally:
        if zip_file:
            zip_file.close()
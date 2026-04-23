def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-v", help="Increase verbosity", action="count")
    parser.add_argument(
        "-s",
        "--source",
        metavar="dir",
        help="The directory containing the repository root",
        type=Path,
        default=None,
    )
    parser.add_argument(
        "-b", "--build", metavar="dir", help="Specify the build directory", type=Path
    )
    parser.add_argument(
        "--arch",
        metavar="architecture",
        help="Specify the target architecture",
        type=str,
        default=None,
    )
    parser.add_argument(
        "--doc-build",
        metavar="dir",
        help="Specify the docs build directory",
        type=Path,
        default=None,
    )
    parser.add_argument(
        "--copy",
        metavar="directory",
        help="The name of the directory to copy an extracted layout to",
        type=Path,
        default=None,
    )
    parser.add_argument(
        "--zip",
        metavar="file",
        help="The ZIP file to write all files to",
        type=Path,
        default=None,
    )
    parser.add_argument(
        "--catalog",
        metavar="file",
        help="The CDF file to write catalog entries to",
        type=Path,
        default=None,
    )
    parser.add_argument(
        "--log",
        metavar="file",
        help="Write all operations to the specified file",
        type=Path,
        default=None,
    )
    parser.add_argument(
        "-t",
        "--temp",
        metavar="file",
        help="A temporary working directory",
        type=Path,
        default=None,
    )
    parser.add_argument(
        "-d", "--debug", help="Include debug build", action="store_true"
    )
    parser.add_argument(
        "-p",
        "--precompile",
        help="Include .pyc files instead of .py",
        action="store_true",
    )
    parser.add_argument(
        "-z", "--zip-lib", help="Include library in a ZIP file", action="store_true"
    )
    parser.add_argument(
        "--flat-dlls", help="Does not create a DLLs directory", action="store_true"
    )
    parser.add_argument(
        "-a",
        "--include-all",
        help="Include all optional components",
        action="store_true",
    )
    parser.add_argument(
        "--include-cat",
        metavar="file",
        help="Specify the catalog file to include",
        type=Path,
        default=None,
    )
    for opt, help in get_argparse_options():
        parser.add_argument(opt, help=help, action="store_true")

    ns = parser.parse_args()
    update_presets(ns)

    ns.source = ns.source or (Path(__file__).resolve().parent.parent.parent)
    ns.build = ns.build or Path(sys.executable).parent
    ns.doc_build = ns.doc_build or (ns.source / "Doc" / "build")
    if ns.copy and not ns.copy.is_absolute():
        ns.copy = (Path.cwd() / ns.copy).resolve()
    if not ns.temp:
        # Put temp on a Dev Drive for speed if we're copying to one.
        # If not, the regular temp dir will have to do.
        if ns.copy and getattr(os.path, "isdevdrive", lambda d: False)(ns.copy):
            ns.temp = ns.copy.with_name(ns.copy.name + "_temp")
        else:
            ns.temp = Path(tempfile.mkdtemp())
    if not ns.source.is_absolute():
        ns.source = (Path.cwd() / ns.source).resolve()
    if not ns.build.is_absolute():
        ns.build = (Path.cwd() / ns.build).resolve()
    if not ns.temp.is_absolute():
        ns.temp = (Path.cwd() / ns.temp).resolve()
    if not ns.doc_build.is_absolute():
        ns.doc_build = (Path.cwd() / ns.doc_build).resolve()
    if ns.include_cat and not ns.include_cat.is_absolute():
        ns.include_cat = (Path.cwd() / ns.include_cat).resolve()
    if ns.zip and not ns.zip.is_absolute():
        ns.zip = (Path.cwd() / ns.zip).resolve()
    if ns.catalog and not ns.catalog.is_absolute():
        ns.catalog = (Path.cwd() / ns.catalog).resolve()

    configure_logger(ns)

    if not ns.arch:
        from .support.arch import calculate_from_build_dir
        ns.arch = calculate_from_build_dir(ns.build)

    expect = f"{VER_MAJOR}.{VER_MINOR}.{VER_MICRO}{VER_SUFFIX}"
    actual = check_patchlevel_version(ns.source)
    if actual and actual != expect:
        log_error(f"Inferred version {expect} does not match {actual} from patchlevel.h. "
                   "You should set %PYTHONINCLUDE% or %PYTHON_HEXVERSION% before launching.")
        return 5

    log_info(
        """OPTIONS
Source: {ns.source}
Build:  {ns.build}
Temp:   {ns.temp}
Arch:   {ns.arch}

Copy to: {ns.copy}
Zip to:  {ns.zip}
Catalog: {ns.catalog}""",
        ns=ns,
    )

    if ns.arch not in ("win32", "amd64", "arm32", "arm64"):
        log_error("--arch is not a valid value (win32, amd64, arm32, arm64)")
        return 4
    if ns.arch == "arm32":
        for n in ("include_idle", "include_tcltk"):
            if getattr(ns, n):
                log_warning(f"Disabling --{n.replace('_', '-')} on unsupported platform")
                setattr(ns, n, False)

    if ns.include_idle and not ns.include_tcltk:
        log_warning("Assuming --include-tcltk to support --include-idle")
        ns.include_tcltk = True

    if not (ns.include_alias or ns.include_alias3 or ns.include_alias3x):
        if ns.include_freethreaded:
            ns.include_alias3x = True
        else:
            ns.include_alias = True

    try:
        generate_source_files(ns)
        files = list(get_layout(ns))
        copy_files(files, ns)
    except KeyboardInterrupt:
        log_info("Interrupted by Ctrl+C")
        return 3
    except SystemExit:
        raise
    except:
        log_exception("Unhandled error")

    if error_was_logged():
        log_error("Errors occurred.")
        return 1
def hipify(
    project_directory: str,
    show_detailed: bool = False,
    extensions: Iterable = (".cu", ".cuh", ".c", ".cc", ".cpp", ".h", ".in", ".hpp"),
    header_extensions: Iterable = (".cuh", ".h", ".hpp"),
    output_directory: str = "",
    header_include_dirs: Iterable = (),
    includes: Iterable = ('*',),
    extra_files: Iterable = (),
    out_of_place_only: bool = False,
    ignores: Iterable = (),
    show_progress: bool = True,
    hip_clang_launch: bool = False,
    is_pytorch_extension: bool = False,
    hipify_extra_files_only: bool = False,
    clean_ctx: GeneratedFileCleaner | None = None
) -> HipifyFinalResult:
    if project_directory == "":
        project_directory = os.getcwd()

    # Verify the project directory exists.
    if not os.path.exists(project_directory):
        print("The project folder specified does not exist.")
        sys.exit(1)

    # If no output directory, provide a default one.
    if not output_directory:
        project_directory.rstrip("/")
        output_directory = project_directory + "_amd"

    if project_directory != output_directory:
        includes = [include.replace(project_directory, output_directory) for include in includes]
        ignores = [ignore.replace(project_directory, output_directory) for ignore in ignores]

    # Copy from project directory to output directory if not done already.
    if not os.path.exists(output_directory):
        shutil.copytree(project_directory, output_directory)

    includes = list(map(_to_unix_path, includes))
    ignores = list(map(_to_unix_path, ignores))

    all_files = list(matched_files_iter(output_directory, includes=includes,
                                        ignores=ignores, extensions=extensions,
                                        out_of_place_only=out_of_place_only,
                                        is_pytorch_extension=is_pytorch_extension))
    all_files_set = set(all_files)

    for f in extra_files:
        if not os.path.isabs(f):
            f = os.path.join(output_directory, f)
        if f not in all_files_set:
            all_files.append(f)

    # List all files in header_include_paths to ensure they are hipified
    from pathlib import Path
    for header_include_dir in header_include_dirs:
        if os.path.isabs(header_include_dir):
            header_include_dir_path = Path(header_include_dir)
        else:
            header_include_dir_path = Path(os.path.join(output_directory, header_include_dir))
        all_files.extend(
            str(path) for path in header_include_dir_path.rglob('*') if path.is_file()
            and _fnmatch(str(path), includes)
            and (not _fnmatch(str(path), ignores))
            and match_extensions(path.name, header_extensions)
        )

    if clean_ctx is None:
        clean_ctx = GeneratedFileCleaner(keep_intermediates=True)

    # Preprocessing statistics.
    stats: dict[str, list] = {"unsupported_calls": [], "kernel_launches": []}

    for filepath in (all_files if not hipify_extra_files_only else extra_files):
        preprocess_file_and_save_result(output_directory, filepath, all_files, header_include_dirs,
                                        stats, hip_clang_launch, is_pytorch_extension, clean_ctx, show_progress)

    print(bcolors.OKGREEN + "Successfully preprocessed all matching files." + bcolors.ENDC, file=sys.stderr)

    # Show detailed summary
    if show_detailed:
        compute_stats(stats)

    return HIPIFY_FINAL_RESULT
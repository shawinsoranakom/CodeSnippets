def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--annotate-diff",
        nargs="*",
        metavar=("BASE_REF", "HEAD_REF"),
        help="Add GitHub Actions annotations on the diff for warnings on "
        "lines changed between the given refs (main and HEAD, by default)",
    )
    parser.add_argument(
        "--fail-if-regression",
        action="store_true",
        help="Fail if known-good files have warnings",
    )
    parser.add_argument(
        "--fail-if-improved",
        action="store_true",
        help="Fail if new files with no nits are found",
    )
    parser.add_argument(
        "--fail-if-new-news-nit",
        metavar="threshold",
        type=int,
        nargs="?",
        const=NEWS_NIT_THRESHOLD,
        help="Fail if new NEWS nit found before threshold line number",
    )

    args = parser.parse_args(argv)
    if args.annotate_diff is not None and len(args.annotate_diff) > 2:
        parser.error(
            "--annotate-diff takes between 0 and 2 ref args, not "
            f"{len(args.annotate_diff)} {tuple(args.annotate_diff)}"
        )
    exit_code = 0

    wrong_directory_msg = "Must run this script from the repo root"
    if not Path("Doc").exists() or not Path("Doc").is_dir():
        raise RuntimeError(wrong_directory_msg)

    warnings = (
        Path("Doc/sphinx-warnings.txt")
        .read_text(encoding="UTF-8")
        .splitlines()
    )

    cwd = str(Path.cwd()) + os.path.sep
    files_with_nits = {
        warning.removeprefix(cwd).split(":")[0]
        for warning in warnings
        if "Doc/" in warning
    }

    with Path("Doc/tools/.nitignore").open(encoding="UTF-8") as clean_files:
        files_with_expected_nits = {
            filename.strip()
            for filename in clean_files
            if filename.strip() and not filename.startswith("#")
        }

    if args.annotate_diff is not None:
        annotate_diff(warnings, *args.annotate_diff)

    if args.fail_if_regression:
        exit_code += fail_if_regression(
            warnings, files_with_expected_nits, files_with_nits
        )

    if args.fail_if_improved:
        exit_code += fail_if_improved(
            files_with_expected_nits, files_with_nits
        )

    if args.fail_if_new_news_nit:
        exit_code += fail_if_new_news_nit(warnings, args.fail_if_new_news_nit)

    return exit_code
def main():
    args = parse_args()
    final_name = args.externals_dir / args.tag

    # Check if the dependency already exists in externals/ directory
    # (either already downloaded/extracted, or checked into the git tree)
    if final_name.exists():
        if args.verbose:
            print(f'{args.tag} already exists at {final_name}, skipping download.')
        return

    # Determine download method: release artifacts for large deps (like LLVM),
    # otherwise zip download from GitHub branches
    if args.release:
        tarball_path = fetch_release(
            args.tag,
            args.externals_dir / 'tarballs',
            org=args.organization,
            verbose=args.verbose,
        )
        extracted = extract_tarball(args.externals_dir, tarball_path, args.tag)
    else:
        # Use zip download from GitHub branches
        # (cpython-bin-deps if --binary, cpython-source-deps otherwise)
        zip_path = fetch_zip(
            args.tag,
            args.externals_dir / 'zips',
            org=args.organization,
            binary=args.binary,
            verbose=args.verbose,
        )
        extracted = extract_zip(args.externals_dir, zip_path)

    if extracted != final_name:
        for wait in [1, 2, 3, 5, 8, 0]:
            try:
                extracted.replace(final_name)
                break
            except PermissionError as ex:
                retry = f" Retrying in {wait}s..." if wait else ""
                print(f"Encountered permission error '{ex}'.{retry}", file=sys.stderr)
                time.sleep(wait)
        else:
            print(
                f"ERROR: Failed to rename {extracted} to {final_name}.",
                "You may need to restart your build",
                file=sys.stderr,
            )
            sys.exit(1)
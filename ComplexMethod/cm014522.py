def main() -> None:
    parser = argparse.ArgumentParser(
        description="Check for missing doc redirects and optionally auto-fix"
    )
    parser.add_argument(
        "--base-ref",
        default="origin/main",
        help="Base git ref to compare against (default: origin/main)",
    )
    parser.add_argument(
        "--redirects-file",
        default="docs/source/redirects.py",
        help="Path to redirects.py (default: docs/source/redirects.py)",
    )
    parser.add_argument(
        "--auto-fix",
        action="store_true",
        help="Automatically add missing redirects for moved files",
    )
    args = parser.parse_args()

    redirects_file = Path(args.redirects_file)
    if not redirects_file.exists():
        print(f"Error: {redirects_file} not found", file=sys.stderr)
        sys.exit(1)

    # Get file changes
    changes = get_doc_changes(args.base_ref)
    if not changes:
        print("✅ No doc files were moved or deleted")
        return

    print(f"Found {len(changes)} moved/deleted doc file(s)")

    # Parse existing redirects
    existing = parse_existing_redirects(redirects_file)
    print(f"Found {len(existing)} existing redirect(s)")

    # Find missing redirects
    missing = find_missing_redirects(changes, existing)

    if not missing:
        print("✅ All moved/deleted doc files have corresponding redirects")
        return

    # Separate auto-fixable (moves with known destination) from manual (deletes)
    auto_fixable = [(k, v) for k, v in missing if v is not None]
    manual_needed = [(k, v) for k, v in missing if v is None]

    # Auto-fix mode
    if args.auto_fix and auto_fixable:
        update_redirects_file(redirects_file, auto_fixable)

        if manual_needed:
            print(f"\n⚠️  {len(manual_needed)} deleted file(s) need manual redirects:")
            for old_key, _ in manual_needed:
                print(f"  • {old_key}")
            print("\nPlease add redirects for deleted files manually.")
            sys.exit(1)
        return

    # Report mode - show what's missing
    print("\n❌ Missing redirects detected!\n")

    for old_key, new_url in missing:
        if new_url:
            print(f"  • MOVED: {old_key} → {new_url}")
        else:
            print(f"  • DELETED: {old_key} (needs manual redirect target)")

    if auto_fixable:
        print("\n📝 Suggested additions to docs/source/redirects.py:\n")
        for old_key, new_url in auto_fixable:
            print(f'    "{old_key}": "{new_url}",')
        print("\n💡 To auto-fix, run:")
        print(
            f"    python3 .github/scripts/check_doc_redirects.py "
            f"--base-ref {args.base_ref} --auto-fix"
        )

    if manual_needed:
        print(f"\n⚠️  {len(manual_needed)} deleted file(s) need manual redirects.")
        print("Please determine appropriate redirect targets for deleted files.")

    sys.exit(1)
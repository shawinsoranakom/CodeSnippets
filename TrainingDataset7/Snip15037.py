def main():
    parser = argparse.ArgumentParser(
        description="Archive Django branches into tags and optionally delete them."
    )
    parser.add_argument(
        "--checkout-dir", required=True, help="Path to Django git checkout"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print commands instead of executing them",
    )
    parser.add_argument(
        "--branches", nargs="*", help="Specific remote branches to include (optional)"
    )
    args = parser.parse_args()

    validate_env(args.checkout_dir)
    dry_run = args.dry_run
    checkout_dir = args.checkout_dir

    if args.branches:
        wanted = set(f"origin/{b}" for b in args.branches)
    else:
        wanted = set()

    branches = get_remote_branches(checkout_dir, include_fn=lambda b: b in wanted)
    if not branches:
        print("No branches matched inclusion criteria.")
        return

    print("\nMatched branches:")
    print("\n".join(branches))
    print()

    branch_updates = {b: get_branch_info(checkout_dir, b) for b in branches}
    print("\nLast updates:")
    for b, (h, d) in branch_updates.items():
        print(f"{b}\t{h}\t{d}")

    if (
        input("\nDelete remote branches and create tags? [y/N]: ").strip().lower()
        == "y"
    ):
        for b, (commit_hash, last_update_date) in branch_updates.items():
            print(f"Creating tag for {b} at {commit_hash=} with {last_update_date=}")
            create_tag(checkout_dir, b, commit_hash, last_update_date, dry_run=dry_run)
            print(f"Deleting remote branch {b}")
            delete_remote_and_local_branch(checkout_dir, b, dry_run=dry_run)
        run(
            ["git", "push", "--tags"],
            cwd=checkout_dir,
            dry_run=dry_run,
        )

    print("Done.")
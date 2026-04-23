def main():
    parser = argparse.ArgumentParser(
        description="Generate block documentation from code introspection"
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help="Output directory for generated docs",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Check if docs are in sync (for CI), exit 1 if not",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Verbose output",
    )

    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(levelname)s: %(message)s",
    )

    print("Loading blocks...")
    blocks = load_all_blocks_for_docs()
    print(f"Found {len(blocks)} blocks")

    if args.check:
        print(f"Checking docs in {args.output_dir}...")
        in_sync = check_docs_in_sync(args.output_dir, blocks)
        if in_sync:
            print("All documentation is in sync!")
            sys.exit(0)
        else:
            print("\n" + "=" * 60)
            print("Documentation is out of sync!")
            print("=" * 60)
            print("\nTo fix this, run one of the following:")
            print("\n  Option 1 - Run locally:")
            print(
                "    cd autogpt_platform/backend && poetry run python scripts/generate_block_docs.py"
            )
            print("\n  Option 2 - Ask Claude Code to run it:")
            print('    "Run the block docs generator script to sync documentation"')
            print("\n" + "=" * 60)
            sys.exit(1)
    else:
        print(f"Generating docs to {args.output_dir}...")
        write_block_docs(
            args.output_dir,
            blocks,
            verbose=args.verbose,
        )
        print("Done!")

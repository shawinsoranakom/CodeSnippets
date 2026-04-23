def main():
    """Main conversion function."""
    parser = create_parser()
    args = parser.parse_args()

    # Get GitHub token
    token = get_github_token()

    # Determine template path
    if args.template.is_absolute():
        template_path = args.template
    else:
        template_path = Path(__file__).parent / args.template

    # Load template
    template = load_template(template_path)

    # Determine what to convert
    markdown_files = []

    if args.files:
        # Convert specific files
        for file_str in args.files:
            file_path = Path(file_str)
            if file_path.exists():
                if file_path.is_file() and file_path.suffix.lower() == '.md':
                    markdown_files.append(file_path)
                else:
                    print(f"Warning: {file_path} is not a markdown file")
            else:
                print(f"Error: {file_path} does not exist")
                sys.exit(1)
    elif args.directory:
        # Convert directory
        recursive = not args.no_recursive
        markdown_files = find_markdown_files(args.directory, recursive)
    else:
        # Convert current directory
        current_dir = Path.cwd()
        markdown_files = find_markdown_files(current_dir, recursive=True)

    if not markdown_files:
        print("No markdown files found to convert.")
        return

    # Validate arguments
    if args.output and len(markdown_files) > 1:
        print("Error: --output can only be used with single file conversion")
        sys.exit(1)

    if args.verbose:
        print(f"Found {len(markdown_files)} markdown files to process:")
        for f in markdown_files:
            print(f"  - {f}")
        print()
    else:
        print(f"Found {len(markdown_files)} markdown files to process")

    # Process files
    successful = 0
    failed = 0

    for file_path in markdown_files:
        # Determine output location
        output_dir = None
        if args.output and len(markdown_files) == 1:
            # Single file with specific output
            output_path = args.output
            if process_single_file_with_output(file_path, template, output_path, token):
                successful += 1
            else:
                failed += 1
        else:
            # Regular processing
            if args.output_dir:
                output_dir = args.output_dir

            if process_file(file_path, template, output_dir, token):
                successful += 1
            else:
                failed += 1

        # Small delay to avoid hitting rate limits
        time.sleep(0.5)

    # Summary
    print(f"\nConversion complete:")
    print(f"✓ Successful: {successful}")
    print(f"✗ Failed: {failed}")

    if failed > 0:
        sys.exit(1)
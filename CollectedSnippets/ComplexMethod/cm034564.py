def main():
    """Main function"""
    try:
        args = parse_arguments()

        # If --list-models is specified, list available models and exit
        if args.list_models:
            print("Available AI models for commit message generation:")
            for model in list_available_models():
                print(f"  - {model}")
            sys.exit(0)

        # Validate and get repository path
        repo_path = validate_git_repository(args.repo)
        repo_info = get_repository_info(repo_path)

        print(f"Repository: {repo_info['name']} ({repo_path})")
        print(f"Branch: {repo_info['branch']}")
        if repo_info['remote'] != "unknown":
            print(f"Remote: {repo_info['remote']}")
        print()

        print("Fetching git diff...")
        diff = get_git_diff(repo_path)

        if diff is None:
            print("Failed to get git diff.")
            sys.exit(1)

        if diff.strip() == "":
            print("No changes staged for commit. Stage changes with 'git add' first.")
            print(f"Run this in the repository: cd {repo_path} && git add <files>")
            sys.exit(0)

        print(f"Using model: {args.model}")
        commit_message = generate_commit_message(diff, args.model, args.max_retries)

        if not commit_message:
            print("Failed to generate commit message after multiple attempts.")
            sys.exit(1)

        if args.edit:
            print("\nOpening editor to modify commit message...")
            commit_message = edit_commit_message(commit_message)
            print("\nEdited commit message:")
            print("-" * 50)
            print(commit_message)
            print("-" * 50)

        if args.no_commit:
            print("\nCommit message generated but not committed (--no-commit flag used).")
            sys.exit(0)

        user_input = input(f"\nDo you want to commit to {repo_info['name']} ({repo_info['branch']})? (y/n): ")
        if user_input.lower() == 'y':
            if make_commit(commit_message, repo_path):
                print("Commit successful!")
            else:
                print("Commit failed.")
                sys.exit(1)
        else:
            print("Commit aborted.")

    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")
        sys.exit(130)
async def main(args: Optional[list[str]] = None):
    """CLI entry point for GitHub Copilot OAuth authentication."""
    import argparse

    parser = argparse.ArgumentParser(
        description="GitHub Copilot OAuth Authentication for gpt4free",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s login                    # Interactive device code login
  %(prog)s status                   # Check authentication status
  %(prog)s logout                   # Remove saved credentials
"""
    )

    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # Login command
    subparsers.add_parser("login", help="Authenticate with GitHub Copilot")

    # Status command
    subparsers.add_parser("status", help="Check authentication status")

    # Logout command
    subparsers.add_parser("logout", help="Remove saved credentials")

    args = parser.parse_args(args)

    if args.command == "login":
        try:
            await GithubCopilot.login()
        except KeyboardInterrupt:
            print("\n\nLogin cancelled.")
            sys.exit(1)
        except Exception as e:
            print(f"\n❌ Login failed: {e}")
            sys.exit(1)

    elif args.command == "status":
        print("\nGitHub Copilot OAuth Status")
        print("=" * 40)

        if GithubCopilot.has_credentials():
            creds_path = GithubCopilot.get_credentials_path()
            print(f"✓ Credentials found at: {creds_path}")

            try:
                with creds_path.open() as f:
                    creds = json.load(f)

                expiry = creds.get("expiry_date")
                if expiry:
                    expiry_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(expiry / 1000))
                    if expiry / 1000 > time.time():
                        print(f"  Token expires: {expiry_time}")
                    else:
                        print(f"  Token expired: {expiry_time}")

                if creds.get("scope"):
                    print(f"  Scope: {creds['scope']}")
            except Exception as e:
                print(f"  (Could not read credential details: {e})")
        else:
            print("✗ No credentials found")
            print(f"\nRun 'g4f auth github-copilot' to authenticate.")

        print()

    elif args.command == "logout":
        print("\nGitHub Copilot OAuth Logout")
        print("=" * 40)

        removed = False

        shared_manager = SharedTokenManager.getInstance()
        path = shared_manager.getCredentialFilePath()

        if path.exists():
            path.unlink()
            print(f"✓ Removed: {path}")
            removed = True

        # Also try the default location
        default_path = Path.home() / ".github-copilot" / "oauth_creds.json"
        if default_path.exists() and default_path != path:
            default_path.unlink()
            print(f"✓ Removed: {default_path}")
            removed = True

        if removed:
            print("\n✓ Credentials removed successfully.")
        else:
            print("No credentials found to remove.")

        print()

    else:
        parser.print_help()
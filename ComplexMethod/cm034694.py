async def main(args: Optional[List[str]] = None):
    """CLI entry point for Antigravity authentication."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Antigravity OAuth Authentication for gpt4free",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s login                    # Interactive login with browser
  %(prog)s login --no-browser       # Manual login (paste URL)
  %(prog)s login --project-id ID    # Login with specific project
  %(prog)s status                   # Check authentication status
  %(prog)s logout                   # Remove saved credentials
"""
    )

    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # Login command
    login_parser = subparsers.add_parser("login", help="Authenticate with Google")
    login_parser.add_argument(
        "--project-id", "-p",
        default="",
        help="Google Cloud project ID (optional, auto-discovered if not set)"
    )
    login_parser.add_argument(
        "--no-browser", "-n",
        action="store_true",
        help="Don't auto-open browser, print URL instead"
    )

    # Status command
    subparsers.add_parser("status", help="Check authentication status")

    # Logout command
    subparsers.add_parser("logout", help="Remove saved credentials")

    args = parser.parse_args(args)

    if args.command == "login":
        try:
            await Antigravity.login(
                project_id=args.project_id,
                no_browser=args.no_browser,
            )
        except KeyboardInterrupt:
            print("\n\nLogin cancelled.")
            sys.exit(1)
        except Exception as e:
            print(f"\n❌ Login failed: {e}")
            sys.exit(1)

    elif args.command == "status":
        print("\nAntigravity Authentication Status")
        print("=" * 40)

        if Antigravity.has_credentials():
            creds_path = Antigravity.get_credentials_path()
            print(f"✓ Credentials found at: {creds_path}")

            # Try to read and display some info
            try:
                with creds_path.open() as f:
                    creds = json.load(f)

                if creds.get("email"):
                    print(f"  Email: {creds['email']}")
                if creds.get("project_id"):
                    print(f"  Project: {creds['project_id']}")

                expiry = creds.get("expiry_date")
                if expiry:
                    expiry_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(expiry / 1000))
                    if expiry / 1000 > time.time():
                        print(f"  Token expires: {expiry_time}")
                    else:
                        print(f"  Token expired: {expiry_time} (will auto-refresh)")
            except Exception as e:
                print(f"  (Could not read credential details: {e})")
        else:
            print("✗ No credentials found")
            print(f"\nRun 'antigravity login' to authenticate.")

        print()

    elif args.command == "logout":
        print("\nAntigravity Logout")
        print("=" * 40)

        removed = False

        # Remove cache file
        cache_path = AntigravityAuthManager.get_cache_file()
        if cache_path.exists():
            cache_path.unlink()
            print(f"✓ Removed: {cache_path}")
            removed = True

        # Remove default credentials file
        default_path = get_antigravity_oauth_creds_path()
        if default_path.exists():
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
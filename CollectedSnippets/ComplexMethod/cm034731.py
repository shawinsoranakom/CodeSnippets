async def main(args: Optional[List[str]] = None):
    """CLI entry point for GeminiCLI authentication."""
    import argparse

    parser = argparse.ArgumentParser(
        description="GeminiCLI OAuth Authentication for gpt4free",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s login                    # Interactive login with browser
  %(prog)s login --no-browser       # Manual login (paste URL)
  %(prog)s status                   # Check authentication status
  %(prog)s logout                   # Remove saved credentials
"""
    )

    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # Login command
    login_parser = subparsers.add_parser("login", help="Authenticate with Google")
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
            await GeminiCLI.login(no_browser=args.no_browser)
        except KeyboardInterrupt:
            print("\n\nLogin cancelled.")
            sys.exit(1)
        except Exception as e:
            print(f"\n❌ Login failed: {e}")
            sys.exit(1)

    elif args.command == "status":
        print("\nGeminiCLI Authentication Status")
        print("=" * 40)

        if GeminiCLI.has_credentials():
            creds_path = GeminiCLI.get_credentials_path()
            print(f"✓ Credentials found at: {creds_path}")

            try:
                with creds_path.open() as f:
                    creds = json.load(f)

                if creds.get("email"):
                    print(f"  Email: {creds['email']}")

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
            print(f"\nRun 'g4f auth gemini-cli login' to authenticate.")

        print()

    elif args.command == "logout":
        print("\nGeminiCLI Logout")
        print("=" * 40)

        removed = False

        cache_path = AuthManager.get_cache_file()
        if cache_path.exists():
            cache_path.unlink()
            print(f"✓ Removed: {cache_path}")
            removed = True

        default_path = get_oauth_creds_path()
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
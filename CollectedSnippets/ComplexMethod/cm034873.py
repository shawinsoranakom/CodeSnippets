def main() -> int:
    parser = argparse.ArgumentParser(
        description="PaddleOCR Document Parsing smoke test"
    )
    parser.add_argument("--test-url", help="Optional: Custom document URL for testing")
    parser.add_argument(
        "--skip-api-test",
        action="store_true",
        help="Skip API connectivity test, only check configuration",
    )
    args = parser.parse_args()

    print("=" * 60)
    print("PaddleOCR Document Parsing - Smoke Test")
    print("=" * 60)

    print("\n[1/3] Checking dependencies...")

    try:
        import httpx

        print(f"  + httpx: {httpx.__version__}")
    except ImportError:
        print("  X httpx not installed")
        print("\nRun this script with uv to auto-resolve dependencies:")
        print("  uv run scripts/smoke_test.py")
        print("\nOr install manually:")
        print("  pip install httpx")
        return 1

    print("\n[2/3] Checking configuration...")

    from lib import get_config

    try:
        api_url, token = get_config()
        print(f"  + PADDLEOCR_DOC_PARSING_API_URL: {api_url}")
        masked_token = token[:8] + "..." + token[-4:] if len(token) > 12 else "***"
        print(f"  + PADDLEOCR_ACCESS_TOKEN: {masked_token}")
    except ValueError as e:
        print(f"  X {e}")
        print_config_guide()
        return 1

    if args.skip_api_test:
        print("\n[3/3] Skipping API connectivity test (--skip-api-test)")
        print("\n" + "=" * 60)
        print("Configuration Check Complete!")
        print("=" * 60)
        return 0

    print("\n[3/3] Testing API connectivity...")

    test_url = (
        args.test_url
        or "https://paddle-model-ecology.bj.bcebos.com/paddlex/imgs/demo_image/pp_structure_v3_demo.png"
    )
    print(f"  Test document: {test_url}")

    from lib import parse_document

    result = parse_document(file_url=test_url)

    if not result.get("ok"):
        error = result.get("error", {})
        print(f"\n  X API call failed: {error.get('message')}")
        if "Authentication" in error.get("message", ""):
            print("\n  Hint: Check if your token is correct and not expired.")
            print(
                "        Get a new token from the PaddleOCR page example code section."
            )
        return 1

    print("  + API call successful!")

    text = result.get("text", "")
    if text:
        preview = text[:200].replace("\n", " ")
        if len(text) > 200:
            preview += "..."
        print(f"\n  Preview: {preview}")

    print("\n" + "=" * 60)
    print("Smoke Test PASSED")
    print("=" * 60)
    print("\nNext steps:")
    print('  uv run scripts/layout_caller.py --file-url "URL" --pretty')
    print('  uv run scripts/layout_caller.py --file-path "doc.pdf" --pretty')
    print(
        "  Results are auto-saved to the system temp directory; the caller prints the saved path."
    )

    return 0
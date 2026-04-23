async def run_tests():
        print("=" * 60)
        print("CDP Cleanup and Browser Reuse Tests")
        print("=" * 60)

        tests = [
            ("WebSocket URL handling", TestCDPWebSocketURL().test_websocket_url_skips_http_verification),
            ("Browser survives after cleanup", TestCDPCleanupOnClose().test_browser_survives_after_cleanup_close),
            ("Sequential connections", TestCDPBrowserReuse().test_sequential_connections_same_browser),
            ("No user wait needed", TestCDPBrowserReuse().test_no_user_wait_needed_between_connections),
            ("HTTP URL with browser_id", TestCDPBackwardCompatibility().test_http_url_with_browser_id_works),
        ]

        results = []
        for name, test_func in tests:
            print(f"\n--- {name} ---")
            try:
                await test_func()
                print(f"PASS")
                results.append((name, True))
            except Exception as e:
                print(f"FAIL: {e}")
                results.append((name, False))

        print("\n" + "=" * 60)
        print("SUMMARY")
        print("=" * 60)
        for name, passed in results:
            print(f"  {name}: {'PASS' if passed else 'FAIL'}")

        all_passed = all(r[1] for r in results)
        print(f"\nOverall: {'ALL TESTS PASSED' if all_passed else 'SOME TESTS FAILED'}")
        return 0 if all_passed else 1
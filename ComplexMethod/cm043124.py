async def main():
    """Run the comparison"""
    print("🤖 Crawl4AI - Bot Detection Test")
    print(f"Testing at: {TEST_URL}")
    print("This site runs various browser fingerprinting tests\n")

    # Test regular browser
    regular_result, regular_detections = await test_browser_mode("Regular Browser")

    # Small delay
    await asyncio.sleep(2)

    # Test undetected browser
    undetected_adapter = UndetectedAdapter()
    undetected_result, undetected_detections = await test_browser_mode(
        "Undetected Browser", 
        undetected_adapter
    )

    # Summary comparison
    print(f"\n{'='*60}")
    print("COMPARISON SUMMARY")
    print(f"{'='*60}")

    print(f"\n{'Test':<25} {'Regular':<15} {'Undetected':<15}")
    print(f"{'-'*55}")

    if regular_detections and undetected_detections:
        print(f"{'WebDriver Detection':<25} {'❌ Detected' if regular_detections['webdriver'] else '✅ Passed':<15} {'❌ Detected' if undetected_detections['webdriver'] else '✅ Passed':<15}")
        print(f"{'Headless Detection':<25} {'❌ Detected' if regular_detections['headless'] else '✅ Passed':<15} {'❌ Detected' if undetected_detections['headless'] else '✅ Passed':<15}")
        print(f"{'Automation Detection':<25} {'❌ Detected' if regular_detections['automation'] else '✅ Passed':<15} {'❌ Detected' if undetected_detections['automation'] else '✅ Passed':<15}")
        print(f"{'Failed Tests':<25} {regular_detections['failed_tests']:<15} {undetected_detections['failed_tests']:<15}")

    print(f"\n{'='*60}")

    if undetected_detections.get('failed_tests', 0) < regular_detections.get('failed_tests', 1):
        print("✅ Undetected browser performed better at evading detection!")
    else:
        print("ℹ️  Both browsers had similar detection results")
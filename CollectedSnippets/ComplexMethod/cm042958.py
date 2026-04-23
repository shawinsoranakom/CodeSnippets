async def test_browser_status_management(manager: BrowserManager):
    """Test browser status and management operations"""
    print(f"\n{INFO}========== Testing Browser Status and Management =========={RESET}")

    # Step 1: Get browser status
    print(f"\n{INFO}1. Getting browser status{RESET}")
    try:
        status = await manager.strategy.get_builtin_browser_status()
        print(f"{SUCCESS}Browser status:{RESET}")
        print(f"  Running: {status['running']}")
        print(f"  CDP URL: {status['cdp_url']}")
    except Exception as e:
        print(f"{ERROR}Failed to get browser status: {str(e)}{RESET}")
        return False

    # Step 2: Test killing the browser
    print(f"\n{INFO}2. Testing killing the browser{RESET}")
    try:
        result = await manager.strategy.kill_builtin_browser()
        if result:
            print(f"{SUCCESS}Browser killed successfully{RESET}")
        else:
            print(f"{ERROR}Failed to kill browser{RESET}")
    except Exception as e:
        print(f"{ERROR}Browser kill operation failed: {str(e)}{RESET}")
        return False

    # Step 3: Check status after kill
    print(f"\n{INFO}3. Checking status after kill{RESET}")
    try:
        status = await manager.strategy.get_builtin_browser_status()
        if not status["running"]:
            print(f"{SUCCESS}Browser is correctly reported as not running{RESET}")
        else:
            print(f"{ERROR}Browser is incorrectly reported as still running{RESET}")
    except Exception as e:
        print(f"{ERROR}Failed to get browser status: {str(e)}{RESET}")
        return False

    # Step 4: Launch a new browser
    print(f"\n{INFO}4. Launching a new browser{RESET}")
    try:
        cdp_url = await manager.strategy.launch_builtin_browser(
            browser_type="chromium", headless=True
        )
        if cdp_url:
            print(f"{SUCCESS}New browser launched at: {cdp_url}{RESET}")
        else:
            print(f"{ERROR}Failed to launch new browser{RESET}")
            return False
    except Exception as e:
        print(f"{ERROR}Browser launch failed: {str(e)}{RESET}")
        return False

    return True
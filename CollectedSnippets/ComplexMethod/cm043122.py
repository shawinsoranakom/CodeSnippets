def analyze_bot_detection(result: CrawlResult) -> dict:
    """Analyze bot detection results from the page"""
    detections = {
        "webdriver": False,
        "headless": False, 
        "automation": False,
        "user_agent": False,
        "total_tests": 0,
        "failed_tests": 0
    }

    if not result.success or not result.html:
        return detections

    # Look for specific test results in the HTML
    html_lower = result.html.lower()

    # Check for common bot indicators
    if "webdriver" in html_lower and ("fail" in html_lower or "true" in html_lower):
        detections["webdriver"] = True
        detections["failed_tests"] += 1

    if "headless" in html_lower and ("fail" in html_lower or "true" in html_lower):
        detections["headless"] = True
        detections["failed_tests"] += 1

    if "automation" in html_lower and "detected" in html_lower:
        detections["automation"] = True
        detections["failed_tests"] += 1

    # Count total tests (approximate)
    detections["total_tests"] = html_lower.count("test") + html_lower.count("check")

    return detections
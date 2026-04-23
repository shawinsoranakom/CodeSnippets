async def main():
    """Run comparison tests on multiple sites"""
    print("🤖 Crawl4AI Browser Adapter Comparison")
    print("Testing regular vs undetected browser modes\n")

    results = {}

    # Test each site
    for site_name, url in TEST_SITES.items():
        regular, undetected = await compare_adapters(url, site_name)
        results[site_name] = {
            "regular": regular,
            "undetected": undetected
        }

        # Delay between different sites
        await asyncio.sleep(3)

    # Final summary
    print(f"\n{'#'*60}")
    print("# FINAL RESULTS")
    print(f"{'#'*60}")
    print(f"{'Site':<30} {'Regular':<15} {'Undetected':<15}")
    print(f"{'-'*60}")

    for site, result in results.items():
        regular_status = "✅ Passed" if result["regular"] else "❌ Blocked"
        undetected_status = "✅ Passed" if result["undetected"] else "❌ Blocked"
        print(f"{site:<30} {regular_status:<15} {undetected_status:<15}")

    # Calculate success rates
    regular_success = sum(1 for r in results.values() if r["regular"])
    undetected_success = sum(1 for r in results.values() if r["undetected"])
    total = len(results)

    print(f"\n{'='*60}")
    print(f"Success Rates:")
    print(f"Regular Adapter: {regular_success}/{total} ({regular_success/total*100:.1f}%)")
    print(f"Undetected Adapter: {undetected_success}/{total} ({undetected_success/total*100:.1f}%)")
    print(f"{'='*60}")
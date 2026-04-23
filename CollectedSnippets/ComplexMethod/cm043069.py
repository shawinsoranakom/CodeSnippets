async def main():
    print("="*60)
    print("TEST 6: Multi-Endpoint Testing")
    print("="*60)

    client = docker.from_env()
    container = None
    monitor_thread = None

    try:
        container = start_container(client, IMAGE, CONTAINER_NAME, PORT)

        print(f"\n⏳ Waiting for permanent browser init (3s)...")
        await asyncio.sleep(3)

        # Start monitoring
        stop_monitoring.clear()
        stats_history.clear()
        monitor_thread = Thread(target=monitor_stats, args=(container,), daemon=True)
        monitor_thread.start()

        await asyncio.sleep(1)
        baseline_mem = stats_history[-1]['memory_mb'] if stats_history else 0
        print(f"📏 Baseline: {baseline_mem:.1f} MB\n")

        base_url = f"http://localhost:{PORT}"

        # Test each endpoint
        endpoints = {
            "/html": test_html,
            "/screenshot": test_screenshot,
            "/pdf": test_pdf,
            "/crawl": test_crawl,
        }

        all_endpoint_stats = {}

        async with httpx.AsyncClient() as http_client:
            for endpoint_name, test_func in endpoints.items():
                print(f"🔄 Testing {endpoint_name} ({REQUESTS_PER_ENDPOINT} requests)...")
                results = await test_func(http_client, base_url, REQUESTS_PER_ENDPOINT)

                successes = sum(1 for r in results if r.get("success"))
                success_rate = (successes / len(results)) * 100
                latencies = [r["latency_ms"] for r in results if "latency_ms" in r]
                avg_lat = sum(latencies) / len(latencies) if latencies else 0

                all_endpoint_stats[endpoint_name] = {
                    'success_rate': success_rate,
                    'avg_latency': avg_lat,
                    'total': len(results),
                    'successes': successes
                }

                print(f"  ✓ Success: {success_rate:.1f}% ({successes}/{len(results)}), Avg: {avg_lat:.0f}ms")

        # Stop monitoring
        await asyncio.sleep(1)
        stop_monitoring.set()
        if monitor_thread:
            monitor_thread.join(timeout=2)

        # Final stats
        memory_samples = [s['memory_mb'] for s in stats_history]
        peak_mem = max(memory_samples) if memory_samples else 0
        final_mem = memory_samples[-1] if memory_samples else 0

        print(f"\n{'='*60}")
        print(f"RESULTS:")
        print(f"{'='*60}")
        for endpoint, stats in all_endpoint_stats.items():
            print(f"  {endpoint:12} Success: {stats['success_rate']:5.1f}%  Avg: {stats['avg_latency']:6.0f}ms")

        print(f"\n  Memory:")
        print(f"    Baseline: {baseline_mem:.1f} MB")
        print(f"    Peak:     {peak_mem:.1f} MB")
        print(f"    Final:    {final_mem:.1f} MB")
        print(f"    Delta:    {final_mem - baseline_mem:+.1f} MB")
        print(f"{'='*60}")

        # Pass/Fail
        passed = True
        for endpoint, stats in all_endpoint_stats.items():
            if stats['success_rate'] < 100:
                print(f"❌ FAIL: {endpoint} success rate {stats['success_rate']:.1f}% < 100%")
                passed = False

        if passed:
            print(f"✅ TEST PASSED")
            return 0
        else:
            return 1

    except Exception as e:
        print(f"\n❌ TEST ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        stop_monitoring.set()
        if container:
            print(f"🛑 Stopping container...")
            container.stop()
            container.remove()
async def main():
    print("="*60)
    print("TEST 5: Pool Stress - Mixed Configs")
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

        url = f"http://localhost:{PORT}/crawl"

        print(f"Testing {len(VIEWPORT_CONFIGS)} different configs:")
        for i, vp in enumerate(VIEWPORT_CONFIGS):
            vp_str = "Default" if vp is None else f"{vp['width']}x{vp['height']}"
            print(f"  {i+1}. {vp_str}")
        print()

        # Run requests: repeat each config REQUESTS_PER_CONFIG times
        all_results = []
        config_sequence = []

        for _ in range(REQUESTS_PER_CONFIG):
            for viewport in VIEWPORT_CONFIGS:
                config_sequence.append(viewport)

        # Shuffle to mix configs
        random.shuffle(config_sequence)

        print(f"🔄 Running {len(config_sequence)} requests with mixed configs...")

        async with httpx.AsyncClient() as http_client:
            for i, viewport in enumerate(config_sequence):
                result = await crawl_with_viewport(http_client, url, viewport)
                all_results.append(result)

                if (i + 1) % 5 == 0:
                    vp_str = "default" if result['viewport'] is None else f"{result['viewport']['width']}x{result['viewport']['height']}"
                    status = "✓" if result.get('success') else "✗"
                    lat = f"{result.get('latency_ms', 0):.0f}ms" if 'latency_ms' in result else "error"
                    print(f"  [{i+1}/{len(config_sequence)}] {status} {vp_str} - {lat}")

        # Stop monitoring
        await asyncio.sleep(2)
        stop_monitoring.set()
        if monitor_thread:
            monitor_thread.join(timeout=2)

        # Analyze results
        pool_stats = analyze_pool_logs(container)

        successes = sum(1 for r in all_results if r.get("success"))
        success_rate = (successes / len(all_results)) * 100
        latencies = [r["latency_ms"] for r in all_results if "latency_ms" in r]
        avg_lat = sum(latencies) / len(latencies) if latencies else 0

        memory_samples = [s['memory_mb'] for s in stats_history]
        peak_mem = max(memory_samples) if memory_samples else 0
        final_mem = memory_samples[-1] if memory_samples else 0

        print(f"\n{'='*60}")
        print(f"RESULTS:")
        print(f"{'='*60}")
        print(f"  Requests:     {len(all_results)}")
        print(f"  Success Rate: {success_rate:.1f}% ({successes}/{len(all_results)})")
        print(f"  Avg Latency:  {avg_lat:.0f}ms")
        print(f"\n  Pool Statistics:")
        print(f"    🔥 Permanent: {pool_stats['permanent']}")
        print(f"    ♨️  Hot:       {pool_stats['hot']}")
        print(f"    ❄️  Cold:      {pool_stats['cold']}")
        print(f"    🆕 New:       {pool_stats['new']}")
        print(f"    ⬆️  Promotions: {pool_stats['promotions']}")
        print(f"    📊 Reuse:     {(pool_stats['total'] / len(all_results) * 100):.1f}%")
        print(f"\n  Memory:")
        print(f"    Baseline: {baseline_mem:.1f} MB")
        print(f"    Peak:     {peak_mem:.1f} MB")
        print(f"    Final:    {final_mem:.1f} MB")
        print(f"    Delta:    {final_mem - baseline_mem:+.1f} MB")
        print(f"{'='*60}")

        # Pass/Fail
        passed = True

        if success_rate < 99:
            print(f"❌ FAIL: Success rate {success_rate:.1f}% < 99%")
            passed = False

        # Should see promotions since we repeat each config 5 times
        if pool_stats['promotions'] < (len(VIEWPORT_CONFIGS) - 1):  # -1 for default
            print(f"⚠️  WARNING: Only {pool_stats['promotions']} promotions (expected ~{len(VIEWPORT_CONFIGS)-1})")

        # Should have created some browsers for different configs
        if pool_stats['new'] == 0:
            print(f"⚠️  NOTE: No new browsers created (all used default?)")

        if pool_stats['permanent'] == len(all_results):
            print(f"⚠️  NOTE: All requests used permanent browser (configs not varying enough?)")

        if final_mem - baseline_mem > 500:
            print(f"⚠️  WARNING: Memory grew {final_mem - baseline_mem:.1f} MB")

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
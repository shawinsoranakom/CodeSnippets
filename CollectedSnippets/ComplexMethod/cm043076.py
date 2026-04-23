async def main():
    print("="*60)
    print("TEST 4: Concurrent Load Testing")
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

        url = f"http://localhost:{PORT}/html"
        payload = {"url": "https://httpbin.org/html"}

        all_results = []
        level_stats = []

        # Run load levels
        for level in LOAD_LEVELS:
            print(f"{'='*60}")
            print(f"🔄 {level['name']} Load: {level['concurrent']} concurrent, {level['requests']} total")
            print(f"{'='*60}")

            start_time = time.time()
            results = await run_concurrent_test(url, payload, level['concurrent'], level['requests'])
            duration = time.time() - start_time

            successes = sum(1 for r in results if r.get("success"))
            success_rate = (successes / len(results)) * 100
            latencies = [r["latency_ms"] for r in results if "latency_ms" in r]
            p50, p95, p99 = calculate_percentiles(latencies)
            avg_lat = sum(latencies) / len(latencies) if latencies else 0

            print(f"  Duration:     {duration:.1f}s")
            print(f"  Success:      {success_rate:.1f}% ({successes}/{len(results)})")
            print(f"  Avg Latency:  {avg_lat:.0f}ms")
            print(f"  P50/P95/P99:  {p50:.0f}ms / {p95:.0f}ms / {p99:.0f}ms")

            level_stats.append({
                'name': level['name'],
                'concurrent': level['concurrent'],
                'success_rate': success_rate,
                'avg_latency': avg_lat,
                'p50': p50, 'p95': p95, 'p99': p99,
            })
            all_results.extend(results)

            await asyncio.sleep(2)  # Cool down between levels

        # Stop monitoring
        await asyncio.sleep(1)
        stop_monitoring.set()
        if monitor_thread:
            monitor_thread.join(timeout=2)

        # Final stats
        pool_stats = count_log_markers(container)
        memory_samples = [s['memory_mb'] for s in stats_history]
        peak_mem = max(memory_samples) if memory_samples else 0
        final_mem = memory_samples[-1] if memory_samples else 0

        print(f"\n{'='*60}")
        print(f"FINAL RESULTS:")
        print(f"{'='*60}")
        print(f"  Total Requests: {len(all_results)}")
        print(f"\n  Pool Utilization:")
        print(f"    🔥 Permanent: {pool_stats['permanent']}")
        print(f"    ♨️  Hot:       {pool_stats['hot']}")
        print(f"    ❄️  Cold:      {pool_stats['cold']}")
        print(f"    🆕 New:       {pool_stats['new']}")
        print(f"\n  Memory:")
        print(f"    Baseline: {baseline_mem:.1f} MB")
        print(f"    Peak:     {peak_mem:.1f} MB")
        print(f"    Final:    {final_mem:.1f} MB")
        print(f"    Delta:    {final_mem - baseline_mem:+.1f} MB")
        print(f"{'='*60}")

        # Pass/Fail
        passed = True
        for ls in level_stats:
            if ls['success_rate'] < 99:
                print(f"❌ FAIL: {ls['name']} success rate {ls['success_rate']:.1f}% < 99%")
                passed = False
            if ls['p99'] > 10000:  # 10s threshold
                print(f"⚠️  WARNING: {ls['name']} P99 latency {ls['p99']:.0f}ms very high")

        if final_mem - baseline_mem > 300:
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
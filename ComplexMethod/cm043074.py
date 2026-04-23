async def main():
    print("="*60)
    print("TEST 3: Pool Validation - Permanent Browser Reuse")
    print("="*60)

    client = docker.from_env()
    container = None
    monitor_thread = None

    try:
        # Start container
        container = start_container(client, IMAGE, CONTAINER_NAME, PORT)

        # Wait for permanent browser initialization
        print(f"\n⏳ Waiting for permanent browser init (3s)...")
        await asyncio.sleep(3)

        # Start stats monitoring
        print(f"📊 Starting stats monitor...")
        stop_monitoring.clear()
        stats_history.clear()
        monitor_thread = Thread(target=monitor_stats, args=(container,), daemon=True)
        monitor_thread.start()

        await asyncio.sleep(1)
        baseline_mem = stats_history[-1]['memory_mb'] if stats_history else 0
        print(f"📏 Baseline (with permanent browser): {baseline_mem:.1f} MB")

        # Test /html endpoint (uses permanent browser for default config)
        print(f"\n🔄 Running {REQUESTS} requests to /html...")
        url = f"http://localhost:{PORT}/html"
        results = await test_endpoint(url, REQUESTS)

        # Wait a bit
        await asyncio.sleep(1)

        # Stop monitoring
        stop_monitoring.set()
        if monitor_thread:
            monitor_thread.join(timeout=2)

        # Analyze logs for pool markers
        print(f"\n📋 Analyzing pool usage...")
        pool_stats = count_log_markers(container)

        # Calculate request stats
        successes = sum(1 for r in results if r.get("success"))
        success_rate = (successes / len(results)) * 100
        latencies = [r["latency_ms"] for r in results if "latency_ms" in r]
        avg_latency = sum(latencies) / len(latencies) if latencies else 0

        # Memory stats
        memory_samples = [s['memory_mb'] for s in stats_history]
        peak_mem = max(memory_samples) if memory_samples else 0
        final_mem = memory_samples[-1] if memory_samples else 0
        mem_delta = final_mem - baseline_mem

        # Calculate reuse rate
        total_requests = len(results)
        total_pool_hits = pool_stats['total_hits']
        reuse_rate = (total_pool_hits / total_requests * 100) if total_requests > 0 else 0

        # Print results
        print(f"\n{'='*60}")
        print(f"RESULTS:")
        print(f"  Success Rate: {success_rate:.1f}% ({successes}/{len(results)})")
        print(f"  Avg Latency:  {avg_latency:.0f}ms")
        print(f"\n  Pool Stats:")
        print(f"    🔥 Permanent Hits: {pool_stats['permanent_hits']}")
        print(f"    ♨️  Hot Pool Hits:   {pool_stats['hot_hits']}")
        print(f"    ❄️  Cold Pool Hits:  {pool_stats['cold_hits']}")
        print(f"    🆕 New Created:    {pool_stats['new_created']}")
        print(f"    📊 Reuse Rate:     {reuse_rate:.1f}%")
        print(f"\n  Memory Stats:")
        print(f"    Baseline: {baseline_mem:.1f} MB")
        print(f"    Peak:     {peak_mem:.1f} MB")
        print(f"    Final:    {final_mem:.1f} MB")
        print(f"    Delta:    {mem_delta:+.1f} MB")
        print(f"{'='*60}")

        # Pass/Fail
        passed = True
        if success_rate < 100:
            print(f"❌ FAIL: Success rate {success_rate:.1f}% < 100%")
            passed = False
        if reuse_rate < 80:
            print(f"❌ FAIL: Reuse rate {reuse_rate:.1f}% < 80% (expected high permanent browser usage)")
            passed = False
        if pool_stats['permanent_hits'] < (total_requests * 0.8):
            print(f"⚠️  WARNING: Only {pool_stats['permanent_hits']} permanent hits out of {total_requests} requests")
        if mem_delta > 200:
            print(f"⚠️  WARNING: Memory grew by {mem_delta:.1f} MB (possible browser leak)")

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
            stop_container(container)
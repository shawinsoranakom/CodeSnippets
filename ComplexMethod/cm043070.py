async def main():
    print("="*60)
    print("TEST 2: Docker Stats Monitoring")
    print("="*60)

    client = docker.from_env()
    container = None
    monitor_thread = None

    try:
        # Start container
        container = start_container(client, IMAGE, CONTAINER_NAME, PORT)

        # Start stats monitoring in background
        print(f"\n📊 Starting stats monitor...")
        stop_monitoring.clear()
        stats_history.clear()
        monitor_thread = Thread(target=monitor_stats, args=(container,), daemon=True)
        monitor_thread.start()

        # Wait a bit for baseline
        await asyncio.sleep(2)
        baseline_mem = stats_history[-1]['memory_mb'] if stats_history else 0
        print(f"📏 Baseline memory: {baseline_mem:.1f} MB")

        # Test /health endpoint
        print(f"\n🔄 Running {REQUESTS} requests to /health...")
        url = f"http://localhost:{PORT}/health"
        results = await test_endpoint(url, REQUESTS)

        # Wait a bit to capture peak
        await asyncio.sleep(1)

        # Stop monitoring
        stop_monitoring.set()
        if monitor_thread:
            monitor_thread.join(timeout=2)

        # Calculate stats
        successes = sum(1 for r in results if r.get("success"))
        success_rate = (successes / len(results)) * 100
        latencies = [r["latency_ms"] for r in results if "latency_ms" in r]
        avg_latency = sum(latencies) / len(latencies) if latencies else 0

        # Memory stats
        memory_samples = [s['memory_mb'] for s in stats_history]
        peak_mem = max(memory_samples) if memory_samples else 0
        final_mem = memory_samples[-1] if memory_samples else 0
        mem_delta = final_mem - baseline_mem

        # Print results
        print(f"\n{'='*60}")
        print(f"RESULTS:")
        print(f"  Success Rate: {success_rate:.1f}% ({successes}/{len(results)})")
        print(f"  Avg Latency:  {avg_latency:.0f}ms")
        print(f"\n  Memory Stats:")
        print(f"    Baseline: {baseline_mem:.1f} MB")
        print(f"    Peak:     {peak_mem:.1f} MB")
        print(f"    Final:    {final_mem:.1f} MB")
        print(f"    Delta:    {mem_delta:+.1f} MB")
        print(f"{'='*60}")

        # Pass/Fail
        if success_rate >= 100 and mem_delta < 100:  # No significant memory growth
            print(f"✅ TEST PASSED")
            return 0
        else:
            if success_rate < 100:
                print(f"❌ TEST FAILED (success rate < 100%)")
            if mem_delta >= 100:
                print(f"⚠️  WARNING: Memory grew by {mem_delta:.1f} MB")
            return 1

    except Exception as e:
        print(f"\n❌ TEST ERROR: {e}")
        return 1
    finally:
        stop_monitoring.set()
        if container:
            stop_container(container)
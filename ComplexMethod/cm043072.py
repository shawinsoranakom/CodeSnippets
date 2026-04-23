async def main():
    print("="*60)
    print("TEST 1: Basic Container Health + Single Endpoint")
    print("="*60)

    client = docker.from_env()
    container = None

    try:
        # Start container
        container = start_container(client, IMAGE, CONTAINER_NAME, PORT)

        # Test /health endpoint
        print(f"\n📊 Testing /health endpoint ({REQUESTS} requests)...")
        url = f"http://localhost:{PORT}/health"
        results = await test_endpoint(url, REQUESTS)

        # Calculate stats
        successes = sum(1 for r in results if r["success"])
        success_rate = (successes / len(results)) * 100
        latencies = [r["latency_ms"] for r in results if r["latency_ms"] is not None]
        avg_latency = sum(latencies) / len(latencies) if latencies else 0

        # Print results
        print(f"\n{'='*60}")
        print(f"RESULTS:")
        print(f"  Success Rate: {success_rate:.1f}% ({successes}/{len(results)})")
        print(f"  Avg Latency:  {avg_latency:.0f}ms")
        if latencies:
            print(f"  Min Latency:  {min(latencies):.0f}ms")
            print(f"  Max Latency:  {max(latencies):.0f}ms")
        print(f"{'='*60}")

        # Pass/Fail
        if success_rate >= 100:
            print(f"✅ TEST PASSED")
            return 0
        else:
            print(f"❌ TEST FAILED (expected 100% success rate)")
            return 1

    except Exception as e:
        print(f"\n❌ TEST ERROR: {e}")
        return 1
    finally:
        if container:
            stop_container(container)
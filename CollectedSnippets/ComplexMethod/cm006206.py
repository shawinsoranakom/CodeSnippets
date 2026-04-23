def main():
    parser = argparse.ArgumentParser(description="Diagnose remote Langflow instance")
    parser.add_argument("--host", required=True, help="Langflow host URL")
    parser.add_argument("--api-key", help="API key for flow execution")
    parser.add_argument("--flow-id", help="Flow ID for testing")
    parser.add_argument("--load-test", type=int, default=0, help="Number of requests for mini load test")
    parser.add_argument("--output", help="Save results to JSON file")

    args = parser.parse_args()

    print(f"🔍 Diagnosing Langflow instance: {args.host}")
    print("=" * 60)

    # Test basic connectivity
    connectivity_results = test_connectivity(args.host)

    # Test flow execution if credentials provided
    flow_results = None
    if args.api_key and args.flow_id:
        flow_results = test_flow_endpoint(args.host, args.api_key, args.flow_id)
    else:
        print("⚠️  Skipping flow test (no API key or flow ID provided)")

    # Run mini load test if requested
    load_results = None
    if args.load_test > 0 and args.api_key and args.flow_id:
        load_results = run_load_simulation(args.host, args.api_key, args.flow_id, args.load_test)

    # Summary
    print("\n" + "=" * 60)
    print("📋 DIAGNOSTIC SUMMARY")
    print("=" * 60)

    print(f"Host: {args.host}")
    print(f"Connectivity: {'✅ OK' if connectivity_results['reachable'] else '❌ FAILED'}")
    print(f"Health Check: {'✅ OK' if connectivity_results['health_check'] else '❌ FAILED'}")

    if connectivity_results["response_time_ms"]:
        print(f"Health Response Time: {connectivity_results['response_time_ms']}ms")

    if flow_results:
        print(f"Flow Execution: {'✅ OK' if flow_results['success'] else '❌ FAILED'}")
        if flow_results["response_time_ms"]:
            print(f"Flow Response Time: {flow_results['response_time_ms']}ms")

    if load_results:
        success_rate = (load_results["successful_requests"] / load_results["total_requests"]) * 100
        print(
            f"Mini Load Test: {load_results['successful_requests']}/{load_results['total_requests']} ({success_rate:.1f}% success)"
        )
        if load_results.get("avg_response_time"):
            print(f"Average Response Time: {load_results['avg_response_time']}ms")

    # Recommendations
    print("\n🔧 RECOMMENDATIONS:")
    if not connectivity_results["reachable"]:
        print("❌ Cannot reach the host - check URL and network connectivity")
    elif not connectivity_results["health_check"]:
        print("❌ Health check failed - Langflow may not be running properly")
    elif flow_results and not flow_results["success"]:
        print("❌ Flow execution failed - check API key, flow ID, and flow configuration")
    elif load_results and load_results["connection_errors"] > 0:
        print("⚠️  Connection errors detected - instance may be overloaded or unstable")
    elif load_results and load_results.get("avg_response_time", 0) > 10000:
        print("⚠️  Slow response times - consider reducing load or optimizing flow")
    else:
        print("✅ Instance appears healthy for load testing")

    # Save results if requested
    if args.output:
        results = {
            "timestamp": time.time(),
            "host": args.host,
            "connectivity": connectivity_results,
            "flow_execution": flow_results,
            "load_simulation": load_results,
        }

        with open(args.output, "w") as f:
            json.dump(results, f, indent=2)
        print(f"\n💾 Results saved to: {args.output}")
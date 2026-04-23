def test_single_request(host):
    """Test a single flow request to ensure the setup works before load testing."""
    import os

    import httpx

    api_key = os.getenv("API_KEY")
    flow_id = os.getenv("FLOW_ID")

    if not api_key or not flow_id:
        print("⚠️  Missing API_KEY or FLOW_ID for test request")
        return False

    print("\n🧪 Testing single request before load test...")
    print(f"   Flow ID: {flow_id}")
    print(f"   API Key: {api_key[:20]}...")

    # First, test basic connectivity
    print("   🔗 Testing basic connectivity...")
    try:
        with httpx.Client(timeout=10.0) as client:
            health_response = client.get(f"{host}/health")
            if health_response.status_code == 200:
                print("   ✅ Health check passed")
            else:
                print(f"   ⚠️  Health check failed: {health_response.status_code}")
                return False
    except Exception as e:
        print(f"   ❌ Connectivity test failed: {e}")
        print(f"      Error type: {type(e).__name__}")
        return False

    # Now test the actual flow request
    print("   🎯 Testing flow request...")
    try:
        url = f"{host}/api/v1/run/{flow_id}?stream=false"
        payload = {
            "input_value": "Hello, this is a test message",
            "output_type": "chat",
            "input_type": "chat",
            "tweaks": {},
        }
        headers = {"x-api-key": api_key, "Content-Type": "application/json"}

        with httpx.Client(timeout=30.0) as client:
            response = client.post(url, json=payload, headers=headers)

            print(f"   📡 Response status: {response.status_code}")

            if response.status_code == 200:
                try:
                    data = response.json()
                    if data.get("outputs"):
                        print("   ✅ Test request successful - flow is working!")
                        return True
                    print(f"   ⚠️  Flow executed but no outputs returned: {data}")
                    return False
                except Exception as e:
                    print(f"   ⚠️  Invalid JSON response: {e}")
                    return False
            else:
                print(f"   ❌ Test request failed: {response.status_code}")
                print(f"   Response: {response.text[:200]}...")
                return False

    except Exception as e:
        print(f"   ❌ Test request error: {e}")
        return False
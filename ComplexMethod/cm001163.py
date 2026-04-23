async def test_graceful_shutdown(test_service):
    """Test that AppService handles graceful shutdown correctly"""
    service, test_service_url = test_service

    # Start a slow request that should complete even after shutdown
    slow_task = asyncio.create_task(send_slow_request(test_service_url))

    # Give the slow request time to start
    await asyncio.sleep(1)

    # Send SIGTERM to the service process
    shutdown_start_time = time.time()
    service.process.terminate()  # This sends SIGTERM

    # Wait a moment for shutdown to start
    await asyncio.sleep(0.5)

    # Try to send a new request - should be rejected or connection refused
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            response = await client.post(f"{test_service_url}/fast_endpoint", json={})
            # Should get 503 Service Unavailable during shutdown
            assert response.status_code == 503
            assert "shutting down" in response.json()["detail"].lower()
    except httpx.ConnectError:
        # Connection refused is also acceptable - server stopped accepting
        pass

    # The slow request should still complete successfully
    slow_result = await slow_task
    assert slow_result["message"] == "completed"
    assert 4.9 < slow_result["duration"] < 5.5  # Should have taken ~5 seconds

    # Wait for the service to fully shut down
    service.process.join(timeout=15)
    shutdown_end_time = time.time()

    # Verify the service actually terminated
    assert not service.process.is_alive()

    # Verify shutdown took reasonable time (slow request - 1s + cleanup)
    shutdown_duration = shutdown_end_time - shutdown_start_time
    assert 4 <= shutdown_duration <= 6  # ~5s request - 1s + buffer

    print(f"Shutdown took {shutdown_duration:.2f} seconds")
    print(f"Slow request completed in: {slow_result['duration']:.2f} seconds")
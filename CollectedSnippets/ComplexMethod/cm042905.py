async def run_memory_stress_test(
    url_count: int = 100,
    target_memory_percent: float = 92.0,  # Push to dangerous levels
    chunk_size: int = 20,  # Larger chunks for more chaos
    aggressive: bool = False,
    spikes: bool = True
):
    test_results = TestResults()
    memory_simulator = MemorySimulator(target_percent=target_memory_percent, aggressive=aggressive)

    logger.info(f"Starting stress test with {url_count} URLs in {'STREAM' if STREAM else 'NON-STREAM'} mode")
    logger.info(f"Target memory usage: {target_memory_percent}%")

    # First, elevate memory usage to create pressure
    logger.info("Creating initial memory pressure...")
    memory_simulator.apply_pressure()

    # Create test URLs in chunks to simulate real-world crawling where URLs are discovered
    all_urls = generate_test_urls(url_count)
    url_chunks = [all_urls[i:i+chunk_size] for i in range(0, len(all_urls), chunk_size)]

    # Set up the crawler components - low memory thresholds to create more requeues
    browser_config = BrowserConfig(headless=True, verbose=False)
    run_config = CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS,
        verbose=False,
        stream=STREAM  # Use the global STREAM variable to set mode
    )

    # Create monitor with reference to test results
    monitor = StressTestMonitor(
        test_results=test_results,
        display_mode=DisplayMode.DETAILED,
        max_visible_rows=20,
        total_urls=url_count  # Pass total URLs count
    )

    # Create dispatcher with EXTREME settings - pure survival mode
    # These settings are designed to create a memory battleground
    dispatcher = MemoryAdaptiveDispatcher(
        memory_threshold_percent=63.0,  # Start throttling at just 60% memory
        critical_threshold_percent=70.0,  # Start requeuing at 70% - incredibly aggressive  
        recovery_threshold_percent=55.0,  # Only resume normal ops when plenty of memory available
        check_interval=0.1,  # Check extremely frequently (100ms)
        max_session_permit=20 if aggressive else 10,  # Double the concurrent sessions - pure chaos
        fairness_timeout=10.0,  # Extremely low timeout - rapid priority changes
        monitor=monitor
    )

    # Set up spike schedule if enabled
    if spikes:
        spike_intervals = []
        # Create 3-5 random spike times
        num_spikes = random.randint(3, 5)
        for _ in range(num_spikes):
            # Schedule spikes at random chunks
            chunk_index = random.randint(1, len(url_chunks) - 1)
            spike_intervals.append(chunk_index)
        logger.info(f"Scheduled memory spikes at chunks: {spike_intervals}")

    try:
        async with AsyncWebCrawler(config=browser_config) as crawler:
            # Process URLs in chunks to simulate discovering URLs over time
            for chunk_index, url_chunk in enumerate(url_chunks):
                logger.info(f"Processing chunk {chunk_index+1}/{len(url_chunks)} ({len(url_chunk)} URLs)")

                # Regular pressure increases
                if chunk_index % 2 == 0:
                    logger.info("Increasing memory pressure...")
                    memory_simulator.apply_pressure()

                # Memory spike if scheduled for this chunk
                if spikes and chunk_index in spike_intervals:
                    logger.info(f"⚠️ CREATING MASSIVE MEMORY SPIKE at chunk {chunk_index+1} ⚠️")
                    # Create a nightmare scenario - multiple overlapping spikes
                    memory_simulator.spike_pressure(duration=10.0)  # 10-second spike

                    # 50% chance of double-spike (pure evil)
                    if random.random() < 0.5:
                        await asyncio.sleep(2.0)  # Wait 2 seconds
                        logger.info("💀 DOUBLE SPIKE - EXTREME MEMORY PRESSURE 💀")
                        memory_simulator.spike_pressure(duration=8.0)  # 8-second overlapping spike

                if STREAM:
                    # Stream mode - process results as they come in
                    async for result in dispatcher.run_urls_stream(
                        urls=url_chunk,
                        crawler=crawler,
                        config=run_config
                    ):
                        await process_result(result, test_results)
                else:
                    # Non-stream mode - get all results at once
                    results = await dispatcher.run_urls(
                        urls=url_chunk,
                        crawler=crawler,
                        config=run_config
                    )
                    await process_results(results, test_results)

                # Simulate discovering more URLs while others are still processing
                await asyncio.sleep(1)

                # RARELY release pressure - make the system fight for resources
                if chunk_index % 5 == 4:  # Less frequent releases
                    release_percent = random.choice([10, 15, 20])  # Smaller, inconsistent releases
                    logger.info(f"Releasing {release_percent}% of memory blocks - brief respite")
                    memory_simulator.release_pressure(percent=release_percent)

    except Exception as e:
        logger.error(f"Test error: {str(e)}")
        raise
    finally:
        # Release memory pressure
        memory_simulator.release_pressure()
        # Log final results
        test_results.log_summary()

        # Check for success criteria
        if len(test_results.completed_urls) + len(test_results.failed_urls) < url_count:
            logger.error(f"TEST FAILED: Not all URLs were processed. {url_count - len(test_results.completed_urls) - len(test_results.failed_urls)} URLs missing.")
            return False

        logger.info("TEST PASSED: All URLs were processed without crashing.")
        return True
def simulate_webcrawler_operations(monitor, num_tasks=20):
    """
    Simulates a web crawler's operations with multiple tasks and different states.

    Args:
        monitor: The CrawlerMonitor instance
        num_tasks: Number of tasks to simulate
    """
    print(f"Starting simulation with {num_tasks} tasks...")

    # Create and register all tasks first
    task_ids = []
    for i in range(num_tasks):
        task_id = str(uuid.uuid4())
        url = f"https://example.com/page{i}"
        monitor.add_task(task_id, url)
        task_ids.append((task_id, url))

        # Small delay between task creation
        time.sleep(0.2)

    # Process tasks with a variety of different behaviors
    threads = []
    for i, (task_id, url) in enumerate(task_ids):
        # Create a thread for each task
        thread = threading.Thread(
            target=process_task,
            args=(monitor, task_id, url, i)
        )
        thread.daemon = True
        threads.append(thread)

    # Start threads in batches to simulate concurrent processing
    batch_size = 4  # Process 4 tasks at a time
    for i in range(0, len(threads), batch_size):
        batch = threads[i:i+batch_size]
        for thread in batch:
            thread.start()
            time.sleep(0.5)  # Stagger thread start times

        # Wait a bit before starting next batch
        time.sleep(random.uniform(1.0, 3.0))

        # Update queue statistics
        update_queue_stats(monitor)

        # Simulate memory pressure changes
        active_threads = [t for t in threads if t.is_alive()]
        if len(active_threads) > 8:
            monitor.update_memory_status("CRITICAL")
        elif len(active_threads) > 4:
            monitor.update_memory_status("PRESSURE")
        else:
            monitor.update_memory_status("NORMAL")

    # Wait for all threads to complete
    for thread in threads:
        thread.join()

    # Final updates
    update_queue_stats(monitor)
    monitor.update_memory_status("NORMAL")

    print("Simulation completed!")
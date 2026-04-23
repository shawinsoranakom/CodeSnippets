def benchmark_dataloader(
    dataset,
    batch_size,
    num_workers,
    num_epochs=1,
    max_batches=10,
    multiprocessing_context=None,
    logging_freq=10,
):
    """Benchmark a dataloader with specific configuration."""
    print("\n--- Benchmarking DataLoader ---")

    # Clear memory before starting
    gc.collect()
    torch.cuda.empty_cache()

    # Create model
    model = create_model()

    # Measure memory before dataloader creation
    memory_before = get_memory_usage()
    print(f"Memory before DataLoader creation: {memory_before:.2f} MB")
    print_detailed_memory()

    # Measure dataloader initialization time
    start = time.perf_counter()
    dataloader = DataLoader(
        dataset,
        batch_size=batch_size,
        shuffle=True,
        num_workers=num_workers,
        pin_memory=torch.cuda.is_available(),
        prefetch_factor=2 if num_workers > 0 else None,
        multiprocessing_context=multiprocessing_context,
    )
    it = iter(dataloader)
    dataloader_init_time = time.perf_counter() - start

    # Measure memory after dataloader creation
    memory_after = get_memory_usage()
    print(f"Memory after DataLoader creation: {memory_after:.2f} MB")
    print(f"Memory increase: {memory_after - memory_before:.2f} MB")

    # Create model and optimizer
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = model.to(device)
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.SGD(model.parameters(), lr=0.01, momentum=0.9)

    # Benchmark dataloading speed
    model.train()
    total_batches = 0
    total_samples = 0
    total_time = 0
    total_data_load_time = 0

    # Measure peak memory during training
    peak_memory = memory_after

    print(
        f"\nStarting training loop with {num_epochs} epochs (max {max_batches} batches per epoch)"
    )

    for epoch in range(num_epochs):
        while total_batches < max_batches:
            batch_start = time.perf_counter()

            try:
                inputs, labels = next(it)
            except StopIteration:
                break

            # Move data to device
            inputs = inputs.to(device)
            labels = labels.to(device)

            # Capture data fetch time (including sending to device)
            data_load_time = time.perf_counter() - batch_start

            # Forward pass
            outputs = model(inputs)
            loss = criterion(outputs, labels)

            # Backward and optimize
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()

            # Capture batch time
            batch_time = time.perf_counter() - batch_start

            total_batches += 1
            total_samples += inputs.size(0)
            total_data_load_time += data_load_time
            total_time += batch_time

            # Update peak memory and log memory usage periodically
            if total_batches % 5 == 0:
                # Force garbage collection before measuring memory
                gc.collect()
                current_memory = get_memory_usage()

                if current_memory > peak_memory:
                    peak_memory = current_memory

            if total_batches % logging_freq == 0:
                print(
                    f"Epoch {epoch + 1}, Batch {total_batches}, "
                    f"Time: {batch_time:.4f}s, "
                    f"Memory: {current_memory:.2f} MB"
                )

    # Calculate statistics
    avg_data_load_time = (
        total_data_load_time / total_batches if total_batches > 0 else 0
    )
    avg_batch_time = total_time / total_batches if total_batches > 0 else 0
    samples_per_second = total_samples / total_time if total_time > 0 else 0

    results = {
        "dataloader_init_time": dataloader_init_time,
        "num_workers": num_workers,
        "batch_size": batch_size,
        "total_batches": total_batches,
        "avg_batch_time": avg_batch_time,
        "avg_data_load_time": avg_data_load_time,
        "samples_per_second": samples_per_second,
        "peak_memory_mb": peak_memory,
        "memory_increase_mb": peak_memory - memory_before,
    }

    print("\nResults:")
    print(f"  DataLoader init time: {dataloader_init_time:.4f} seconds")
    print(f"  Average data loading time: {avg_data_load_time:.4f} seconds")
    print(f"  Average batch time: {avg_batch_time:.4f} seconds")
    print(f"  Samples per second: {samples_per_second:.2f}")
    print(f"  Peak memory usage: {peak_memory:.2f} MB")
    print(f"  Memory increase: {peak_memory - memory_before:.2f} MB")

    # Clean up
    del model, optimizer
    del dataloader

    # Force garbage collection
    gc.collect()
    torch.cuda.empty_cache()

    return results
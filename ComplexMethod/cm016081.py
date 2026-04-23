def test_benchmark_tile_reduce_various_sizes(self) -> None:
        """
        Benchmark tile reduce across various matrix sizes.
        """
        # Test various matrix sizes
        tile_sizes = [512, 1024, 2048, 4096, 8192, 16384]
        full_size = tile_sizes[-1]
        warmup_iters = 5
        bench_iters = 20

        results = []

        for tile_size in tile_sizes:
            try:
                result = self._benchmark_tile_reduce_single(
                    full_size, tile_size, warmup_iters, bench_iters
                )
                results.append(result)

                if self.rank == 0:
                    print(
                        f"Matrix Size: {full_size}x{full_size}, Tile Size: {tile_size}x{tile_size}"
                    )
                    print(
                        f"  Mean Time: {result['mean_time_ms']:.3f} ± {result['std_time_ms']:.3f} ms"
                    )
                    print(f"  Throughput: {result['throughput_gb_s']:.2f} GB/s")
                    print(f"  Bytes: {result['tile_bytes']:.0f}")
                    print()

            except Exception as e:
                if self.rank == 0:
                    print(f"Failed to benchmark matrix size {full_size}: {e}")

        # Print summary
        if self.rank == 0 and results:
            print("=== BENCHMARK SUMMARY ===")
            print(
                f"{'Matrix Size':<12} {'Tile Size':<10} {'Time (ms)':<12} {'Throughput (GB/s)':<18} {'Bytes':<15}"
            )
            print("-" * 70)

            for result in results:
                print(
                    f"{result['full_size']}x{result['full_size']:<7} "
                    f"{result['tile_size']}x{result['tile_size']:<5} "
                    f"{result['mean_time_ms']:<12.3f} "
                    f"{result['throughput_gb_s']:<18.2f} "
                    f"{result['tile_bytes']:<15.0f}"
                )
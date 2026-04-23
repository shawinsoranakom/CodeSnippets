def test_shrink_group_vs_abort_reinit_performance(self):
        """Compare performance of shrink_group vs traditional abort+reinit (simplified for reliability)."""
        log_test_info(self.rank, "=== TEST 1: abort+reinit ===")

        device, pg1 = self._setup_shrink_test("_perf_reinit")
        torch.cuda.synchronize(device)

        # Test 1: Traditional abort + reinit
        start_time = time.perf_counter()
        dist.destroy_process_group()

        device, new_pg = self._setup_shrink_test("perf_shrink_test1")
        reinit_time = time.perf_counter() - start_time

        # Test collective with original rank values for fair comparison (non-blocking mode)
        test_tensor = torch.full((1,), self.rank, device=device, dtype=torch.float32)
        work = c10d.all_reduce(test_tensor, group=new_pg, async_op=True)
        work.wait()

        torch.cuda.synchronize(device)

        # Verify correctness
        expected_sum = sum(r for r in range(self.world_size))
        self.assertEqual(test_tensor.item(), expected_sum, "Reinit collective failed")

        log_test_info(self.rank, f"abort+reinit: {reinit_time:.4f}s")
        dist.destroy_process_group(new_pg)

        # Test 2: shrink_group with NCCL_SHRINK_ABORT
        log_test_info(self.rank, "=== TEST 2: shrink_group ===")

        ranks_to_exclude = [self.world_size - 1]
        is_excluded = self.rank in ranks_to_exclude
        log_test_info(
            self.rank,
            f"Excluding ranks: {ranks_to_exclude}, am_excluded: {is_excluded}",
        )

        device, pg1 = self._setup_shrink_test("perf_shrink_test2")  # Unique suffix

        shrink_time = 0
        if not is_excluded:
            torch.cuda.synchronize(device)  # Ensure accurate timing
            start_time = time.perf_counter()
            shrunk_pg = c10d.shrink_group(
                ranks_to_exclude, shrink_flags=NCCL_SHRINK_ABORT
            )
            c10d.all_reduce(torch.ones(1).cuda(device), group=shrunk_pg)
            shrink_time = time.perf_counter() - start_time

            # Test collective communication on shrunk group (non-blocking mode)
            test_tensor = torch.full(
                (1,), self.rank, device=device, dtype=torch.float32
            )
            work = c10d.all_reduce(test_tensor, group=shrunk_pg, async_op=True)
            work.wait()

            # Verify correctness
            expected_sum = sum(
                r for r in range(self.world_size) if r not in ranks_to_exclude
            )
            self.assertEqual(
                test_tensor.item(),
                expected_sum,
                "shrink_test: collective result mismatch",
            )

            torch.cuda.synchronize(device)  # Ensure operations complete
            log_test_info(self.rank, f"shrink_group: {shrink_time:.4f}s")
            dist.destroy_process_group()
        else:
            log_test_info(self.rank, "Excluded from shrink test - exiting immediately")
            dist.destroy_process_group()
            return

        # Performance analysis (only for participating ranks)
        if shrink_time > 0 and reinit_time > 0:
            speedup = reinit_time / shrink_time
            time_saved = reinit_time - shrink_time

            log_test_info(self.rank, "=== PERFORMANCE RESULTS ===")
            log_test_info(self.rank, f"shrink_group:  {shrink_time:.4f}s")
            log_test_info(self.rank, f"abort+reinit:  {reinit_time:.4f}s")
            log_test_info(self.rank, f"time_saved:    {time_saved:+.4f}s")
            log_test_info(self.rank, f"speedup:       {speedup:.2f}x")

            if speedup > 1.1:
                log_test_success(self.rank, "shrink_group significantly faster")
            elif speedup > 0.9:
                log_test_info(self.rank, "≈ comparable performance")
            else:
                log_test_warning(self.rank, "abort+reinit faster")

        log_test_info(self.rank, "Performance test completed")
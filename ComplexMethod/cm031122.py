def test_same_thread_id_multiple_interpreters_stress(self):
        """Stress test: same thread_id across multiple interpreters with interleaved samples.

        This test catches bugs where thread state is keyed only by thread_id
        without considering interpreter_id (both in writer and reader).
        """
        random.seed(999)

        # Multiple interpreters, each with overlapping thread_ids
        interp_ids = [0, 1, 2, 3]
        # Same thread_ids used across all interpreters
        shared_thread_ids = [1, 2, 3]

        filenames = [f"file{i}.py" for i in range(10)]
        funcnames = [f"func{i}" for i in range(15)]
        statuses = [0, THREAD_STATUS_HAS_GIL, THREAD_STATUS_ON_CPU]

        samples = []
        for i in range(1000):
            # Randomly pick an interpreter
            iid = random.choice(interp_ids)
            # Randomly pick 1-3 threads (from shared pool)
            num_threads = random.randint(1, 3)
            selected_tids = random.sample(shared_thread_ids, num_threads)

            threads = []
            for tid in selected_tids:
                status = random.choice(statuses)
                depth = random.randint(1, 6)
                frames = []
                for d in range(depth):
                    # Include interpreter and thread info in frame data for verification
                    fname = f"i{iid}_t{tid}_{random.choice(filenames)}"
                    func = random.choice(funcnames)
                    lineno = i * 10 + d + 1  # Unique per sample
                    frames.append(make_frame(fname, lineno, func))
                threads.append(make_thread(tid, frames, status))

            samples.append([make_interpreter(iid, threads)])

        collector, count = self.roundtrip(samples, compression="zstd")
        self.assertGreater(count, 0)
        self.assert_samples_equal(samples, collector)

        # Verify that we have samples from multiple (interpreter, thread) combinations
        # with the same thread_id
        keys = set(collector.by_thread.keys())
        # Should have samples for same thread_id in different interpreters
        for tid in shared_thread_ids:
            interps_with_tid = [iid for (iid, t) in keys if t == tid]
            self.assertGreater(
                len(interps_with_tid),
                1,
                f"Thread {tid} should appear in multiple interpreters",
            )
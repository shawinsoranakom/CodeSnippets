def test_encoding_transitions_stress(self):
        """Stress test stack encoding transitions."""
        random.seed(789)

        base_frames = [
            make_frame(f"base{i}.py", i, f"base{i}") for i in range(5)
        ]
        samples = []

        for i in range(200):
            choice = random.randint(0, 4)
            if choice == 0:
                # Full new stack
                depth = random.randint(1, 8)
                frames = [
                    make_frame(f"new{i}_{j}.py", j, f"new{j}")
                    for j in range(depth)
                ]
            elif choice == 1:
                # Repeat previous (will use RLE if identical)
                frames = base_frames[: random.randint(1, 5)]
            elif choice == 2:
                # Add frames on top (suffix encoding)
                extra = random.randint(1, 3)
                frames = [
                    make_frame(f"top{i}_{j}.py", j, f"top{j}")
                    for j in range(extra)
                ]
                frames.extend(base_frames[: random.randint(2, 4)])
            else:
                # Pop and push (pop-push encoding)
                keep = random.randint(1, 3)
                push = random.randint(0, 2)
                frames = [
                    make_frame(f"push{i}_{j}.py", j, f"push{j}")
                    for j in range(push)
                ]
                frames.extend(base_frames[:keep])

            samples.append([make_interpreter(0, [make_thread(1, frames)])])

        collector, count = self.roundtrip(samples)
        self.assertEqual(count, len(samples))
        self.assert_samples_equal(samples, collector)
def test_ops_append_to_existing_file_tunableop(self, device, dtype):
        """If a TunableOp results file already exists (with matching Validator),
        new results should be appended (not overwritten)."""

        with self._tunableop_ctx():
            torch.cuda.tunable.set_rotating_buffer_size(0)

            # Seed the existing results file with Validator lines + 1 result line
            results_filename = torch.cuda.tunable.get_filename()
            validators = torch.cuda.tunable.get_validators()  # Iterable[Tuple[str, str]]

            seed_lines = []
            # Each (k, v) becomes a "Validator" line
            for k, v in validators:
                seed_lines.append(f"Validator,{k},{v}")

            # One arbitrary, plausible matmul result line
            seed_lines.append(
                "GemmAndBiasTunableOp_float_TN,tn_768_32_1024_ld_1024_1024_768,"
                "Gemm_Hipblaslt_220580,0.0103395"
            )

            with open(results_filename, "w") as f:
                f.write("\n".join(seed_lines) + "\n")

            # Count initial (non-Validator) lines
            with open(results_filename) as f:
                initial_content = f.read()
            initial_lines = [
                l for l in initial_content.split("\n")
                if l and not l.startswith("Validator")
            ]
            initial_count = len(initial_lines)
            self.assertGreater(initial_count, 0)  # we seeded 1 result line

            # Perform ONE simple matmul
            A = torch.randn(27, 43, device=device, dtype=dtype)
            B = torch.randn(43, 39, device=device, dtype=dtype)
            _ = torch.matmul(A, B)

            # Verify that new results were appended to the same file
            with open(results_filename) as f:
                final_content = f.read()
            final_lines = [
                l for l in final_content.split("\n")
                if l and not l.startswith("Validator")
            ]
            final_count = len(final_lines)

            self.assertGreater(final_count, initial_count)
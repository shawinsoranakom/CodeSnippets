def generate_mm_shapes(self) -> Generator[tuple[int, int, int, Any], None, None]:
        """Generator that yields (m, k, n, dtype) tuples for matrix multiplication.

        First exhausts all shapes from additional_shape_collections, then generates random shapes.
        Only yields unaligned shapes since external CSV shapes may not be pre-filtered.
        """
        # Phase 1: Use all shapes from additional shape collections
        for collection in self.additional_shape_collections:
            for m, k, n, dtype1, _ in collection:
                # Filter for unaligned shapes only (external CSVs may not be pre-filtered)
                align_size = get_alignment_size_dtype(dtype1)
                if not all(self.is_aligned(dim, align_size) for dim in [m, k, n]):
                    # Check if it fits in memory
                    if fits_in_memory(dtype1, m, k, n):
                        yield (m, k, n, dtype1)

        # Phase 2: Generate infinite random shapes

        while True:
            # Generate random dtype
            dtype_choices = [torch.float16, torch.bfloat16, torch.float32]
            dtype = random.choices(dtype_choices)[0]

            # Generate random shape for this dtype
            uniform = random.choices([True, False])[0]
            align_size = get_alignment_size_dtype(dtype)

            # Keep trying until we get a valid unaligned shape that fits in memory
            while True:
                if uniform:
                    m = random.randint(1, 65536)
                    k = random.randint(1, 65536)
                    n = random.randint(1, 65536)
                else:
                    m = self.get_random_dim()
                    k = self.get_random_dim()
                    n = self.get_random_dim()

                # Skip if all dimensions are aligned (we need unaligned for padding to be relevant)
                if all(self.is_aligned(dim, align_size) for dim in [m, k, n]):
                    continue

                # Check if it fits in memory
                if fits_in_memory(dtype, m, k, n):
                    yield (m, k, n, dtype)
                    break
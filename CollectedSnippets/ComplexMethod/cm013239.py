def __exit__(self, exc_type, exc_value, traceback):
        # Don't check for leaks if an exception was thrown
        if exc_type is not None:
            return

        # Compares caching allocator before/after statistics
        # An increase in allocated memory is a discrepancy indicating a possible
        #   memory leak
        discrepancy_detected = False
        num_devices = torch.cuda.device_count()
        for i in range(num_devices):
            # avoid counting cublasWorkspace allocations
            torch._C._cuda_clearCublasWorkspaces()
            caching_allocator_mem_allocated = torch.cuda.memory_allocated(i)

            if caching_allocator_mem_allocated > self.caching_allocator_befores[i]:
                discrepancy_detected = True
                break

        # Short-circuits if no discrepancy detected
        if not discrepancy_detected:
            return

        # Validates the discrepancy persists after garbage collection and
        #   is confirmed by the driver API

        # NOTE: driver API iscrepancies alone are ignored because with the jiterator
        #   some tests may permanently increase the CUDA context size and
        #   that will appear as a driver memory leak but is the expected behavior.

        # GCs and clears the cache
        gc.collect()
        torch.cuda.empty_cache()

        for i in range(num_devices):

            discrepancy_detected = True

            # Query memory multiple items to ensure leak was not transient
            for _ in range(3):
                caching_allocator_mem_allocated = torch.cuda.memory_allocated(i)
                bytes_free, bytes_total = torch.cuda.mem_get_info(i)
                driver_mem_allocated = bytes_total - bytes_free

                caching_allocator_discrepancy = False
                driver_discrepancy = False

                if caching_allocator_mem_allocated > self.caching_allocator_befores[i]:
                    caching_allocator_discrepancy = True

                if driver_mem_allocated > self.driver_befores[i]:
                    driver_discrepancy = True

                if not (caching_allocator_discrepancy or driver_discrepancy):
                    # Leak was false positive, exit loop
                    discrepancy_detected = False
                    break

            if not discrepancy_detected:
                continue

            if caching_allocator_discrepancy and not driver_discrepancy:  # type: ignore[possibly-undefined]
                # Just raises a warning if the leak is not validated by the
                #   driver API
                # NOTE: this may be a problem with how the caching allocator collects its
                #   statistics or a leak too small to trigger the allocation of an
                #   additional block of memory by the CUDA driver
                msg = ("CUDA caching allocator reports a memory leak not "  # type: ignore[possibly-undefined]
                       f"verified by the driver API in {self.name}! "
                       f"Caching allocator allocated memory was {self.caching_allocator_befores[i]} "
                       f"and is now reported as {caching_allocator_mem_allocated} "  # type: ignore[possibly-undefined]
                       f"on device {i}. "
                       f"CUDA driver allocated memory was {self.driver_befores[i]} and is now {driver_mem_allocated}.")  # type: ignore[possibly-undefined]
                warnings.warn(msg, stacklevel=2)
            elif caching_allocator_discrepancy and driver_discrepancy:  # type: ignore[possibly-undefined]
                # A caching allocator discrepancy validated by the driver API is a
                #   failure (except on ROCm, see below)
                msg = (f"CUDA driver API confirmed a leak in {self.name}! "  # type: ignore[possibly-undefined]
                       f"Caching allocator allocated memory was {self.caching_allocator_befores[i]} "
                       f"and is now reported as {caching_allocator_mem_allocated} "  # type: ignore[possibly-undefined]
                       f"on device {i}. "
                       f"CUDA driver allocated memory was {self.driver_befores[i]} and is now {driver_mem_allocated}.")  # type: ignore[possibly-undefined]

                raise RuntimeError(msg)
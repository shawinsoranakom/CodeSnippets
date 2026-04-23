def __exit__(self, exc_type, exc_value, traceback):
        # Don't check for leaks if an exception was thrown
        if exc_type is not None:
            return
        # Compares caching allocator before/after statistics
        # An increase in allocated memory is a discrepancy indicating a possible memory leak
        discrepancy_detected = False
        caching_allocator_mem_allocated = torch.mps.current_allocated_memory()
        if caching_allocator_mem_allocated > self.caching_allocator_before:
            discrepancy_detected = True

        # Short-circuits if no discrepancy detected
        if not discrepancy_detected:
            return
        # Validates the discrepancy persists after garbage collection and
        # is confirmed by the driver API
        gc.collect()
        torch.mps.empty_cache()

        discrepancy_detected = True
        # Query memory multiple items to ensure leak was not transient
        for _ in range(3):
            caching_allocator_mem_allocated = torch.mps.current_allocated_memory()
            driver_mem_allocated = torch.mps.driver_allocated_memory()

            caching_allocator_discrepancy = False
            driver_discrepancy = False

            if caching_allocator_mem_allocated > self.caching_allocator_before:
                caching_allocator_discrepancy = True

            if driver_mem_allocated > self.driver_before:
                driver_discrepancy = True

            if not (caching_allocator_discrepancy or driver_discrepancy):
                # Leak was false positive, exit loop
                discrepancy_detected = False
                break

        if caching_allocator_discrepancy and not driver_discrepancy:
            # Just raises a warning if the leak is not validated by the driver API
            msg = ("MPS caching allocator reports a memory leak not "
                   f"verified by the driver API in {self.name}! "
                   f"Caching allocator allocated memory was {self.caching_allocator_before} "
                   f"and is now reported as {caching_allocator_mem_allocated}. "
                   f"MPS driver allocated memory was {self.driver_before} and is now {driver_mem_allocated}.")
            warnings.warn(msg)
        elif caching_allocator_discrepancy and driver_discrepancy:
            # A caching allocator discrepancy validated by the driver API is a failure
            msg = (f"MPS driver API confirmed a leak in {self.name}! "
                   f"Caching allocator allocated memory was {self.caching_allocator_before} "
                   f"and is now reported as {caching_allocator_mem_allocated}. "
                   f"MPS driver allocated memory was {self.driver_before} and is now {driver_mem_allocated}.")

            raise RuntimeError(msg)
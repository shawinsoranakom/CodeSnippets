def barrier(self, timeout: float = 30.0):
        """A robust barrier to synchronize all ranks.


        Uses a multi-phase approach to ensure all processes reach the barrier
        before proceeding:

        1. Each process signals it has reached the barrier

        2. Each process signals that it has confirmed the arrival of all other
        ranks.

        3. Rank 0 waits for all other ranks to signal their departure to ensure
        that all ranks have departed the barrier first.

        Args:
            timeout: Maximum time in seconds to wait for each phase (in seconds)


        Raises:
            RuntimeError: If coordination fails or times out
        """
        # Generate a barrier ID that is globally unique
        try:
            if self.rank == 0:
                barrier_id = f"barrier_{uuid.uuid4()}"
                self.broadcast_obj(barrier_id, src=0)
            else:
                barrier_id = self.broadcast_obj(None, src=0)
        except Exception as e:
            raise RuntimeError("Failed to broadcast barrier_id") from e

        # Phase 1: Signal arrival at barrier
        # Wait for all processes to arrive
        # We need all ranks to confirm the arrival of all other ranks.
        # This is the key synchronization point.
        arrival_key = f"arrival_{barrier_id}_{self.rank}"
        try:
            self.store.set(arrival_key, b"1")
        except Exception as e:
            raise RuntimeError("Failed to signal barrier arrival") from e

        start_time = time.time()
        processes_arrived: set[int] = set()

        while len(processes_arrived) < self.world_size:
            # Check for timeout
            cur_time = time.time()
            if cur_time - start_time > timeout:
                raise RuntimeError(f"Barrier timed out after {timeout:.2f} seconds")

            # Check for each process
            for i in range(self.world_size):
                if i in processes_arrived:
                    continue

                key = f"arrival_{barrier_id}_{i}"
                try:
                    # Try to get the key - if it exists, we'll get a value
                    # If it doesn't exist, it will throw an exception
                    self.store.get(key)
                    processes_arrived.add(i)
                except KeyError:
                    # Key doesn't exist yet
                    pass
                except Exception as check_e:
                    logger.debug("Error checking key existence: %s", check_e)
                    sched_yield()

            # Short sleep to avoid tight polling
            if len(processes_arrived) < self.world_size:
                sched_yield()

        # Phase 2: Signal departure from barrier
        # We only care to block at this stage in rank 0, which runs the
        # server side of the TCPStore. We want to make sure that all
        # clients have departed the barrier before rank 0 in case the
        # next thing after the barrier is a shutdown, including tearing
        # down the TCPStore. Other ranks can exit the barrier immediately
        # after signaling their departure.
        departure_key = f"departure_{barrier_id}_{self.rank}"
        try:
            self.store.set(departure_key, b"1")
        except Exception as e:
            raise RuntimeError("Failed to signal barrier departure") from e

        if self.rank != 0:
            return

        # Make rank 0 wait for all processes to signal departure
        start_time = time.time()
        processes_departed: set[int] = set()

        while len(processes_departed) < self.world_size:
            # Check for timeout
            if time.time() - start_time > timeout:
                raise RuntimeError(
                    f"Barrier departure timed out after {timeout:.2f} seconds"
                )

            # Check for each process
            for i in range(self.world_size):
                if i in processes_departed:
                    continue

                key = f"departure_{barrier_id}_{i}"
                try:
                    # Try to get the key - if it exists, we'll get a value
                    # If it doesn't exist, it will throw an exception
                    self.store.get(key)
                    processes_departed.add(i)
                except KeyError:
                    # Key doesn't exist yet
                    pass
                except Exception as check_e:
                    logger.debug("Error checking key existence: %s", check_e)
                    sched_yield()

            # Short sleep to avoid tight polling
            if len(processes_departed) < self.world_size:
                sched_yield()

        # Clean up keys to avoid leaking memory in the store
        for i in range(self.world_size):
            try:
                self.store.delete_key(f"arrival_{barrier_id}_{i}")
            except Exception:
                logger.debug("Error deleting key: %s", f"arrival_{barrier_id}_{i}")

            try:
                self.store.delete_key(f"departure_{barrier_id}_{i}")
            except Exception:
                logger.debug("Error deleting key: %s", f"departure_{barrier_id}_{i}")
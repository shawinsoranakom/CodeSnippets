def assert_races_do_not_crash(
        self, opname, get_items, read, write, *, check_items=False
    ):
        # This might need a few dozen loops in some cases:
        for _ in range(self.LOOPS):
            items = get_items()
            # Reset:
            if check_items:
                for item in items:
                    reset_code(item)
            else:
                reset_code(read)
            # Specialize:
            for _ in range(_testinternalcapi.SPECIALIZATION_THRESHOLD):
                read(items)
            if check_items:
                for item in items:
                    self.assert_specialized(item, opname)
            else:
                self.assert_specialized(read, opname)
            # Create writers:
            writers = []
            for _ in range(self.WRITERS):
                writer = threading.Thread(target=write, args=[items])
                writers.append(writer)
            # Run:
            for writer in writers:
                writer.start()
            read(items)  # BOOM!
            for writer in writers:
                writer.join()
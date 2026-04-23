def racing_creation(self, cls, set=setattr):
        objects = []
        processed = []

        OBJECT_COUNT = 100
        THREAD_COUNT = 10
        CUR = 0

        for i in range(OBJECT_COUNT):
            objects.append(cls())

        def writer_func(name):
            last = -1
            while True:
                if CUR == last:
                    time.sleep(0.001)
                    continue
                elif CUR == OBJECT_COUNT:
                    break

                obj = objects[CUR]
                set(obj, name, name)
                last = CUR
                processed.append(name)

        writers = []
        for x in range(THREAD_COUNT):
            writer = Thread(target=partial(writer_func, f"a{x:02}"))
            writers.append(writer)
            writer.start()

        for i in range(OBJECT_COUNT):
            CUR = i
            while len(processed) != THREAD_COUNT:
                time.sleep(0.001)
            processed.clear()

        CUR = OBJECT_COUNT

        for writer in writers:
            writer.join()

        for obj_idx, obj in enumerate(objects):
            assert (
                len(obj.__dict__) == THREAD_COUNT
            ), f"{len(obj.__dict__)} {obj.__dict__!r} {obj_idx}"
            for i in range(THREAD_COUNT):
                assert f"a{i:02}" in obj.__dict__, f"a{i:02} missing at {obj_idx}"
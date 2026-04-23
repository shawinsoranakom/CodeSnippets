def test_racing_set_object_dict(self):
        """Races assigning to __dict__ should be thread safe"""
        class C: pass
        class MyDict(dict): pass
        for cyclic in (False, True):
            f = C()
            f.__dict__ = {"foo": 42}
            THREAD_COUNT = 10

            def writer_func(l):
                for i in range(1000):
                    if cyclic:
                        other_d = {}
                    d = MyDict({"foo": 100})
                    if cyclic:
                        d["x"] = other_d
                        other_d["bar"] = d
                    l.append(weakref.ref(d))
                    f.__dict__ = d

            def reader_func():
                for i in range(1000):
                    f.foo

            lists = []
            readers = []
            writers = []
            for x in range(THREAD_COUNT):
                thread_list = []
                lists.append(thread_list)
                writer = Thread(target=partial(writer_func, thread_list))
                writers.append(writer)

            for x in range(THREAD_COUNT):
                reader = Thread(target=partial(reader_func))
                readers.append(reader)

            for writer in writers:
                writer.start()
            for reader in readers:
                reader.start()

            for writer in writers:
                writer.join()

            for reader in readers:
                reader.join()

            f.__dict__ = {}
            gc.collect()
            gc.collect()

            count = 0
            ids = set()
            for thread_list in lists:
                for i, ref in enumerate(thread_list):
                    if ref() is None:
                        continue
                    count += 1
                    ids.add(id(ref()))
                    count += 1

            self.assertEqual(count, 0)
def test_heap(self):
        iterations = 5000
        maxblocks = 50
        blocks = []

        # get the heap object
        heap = multiprocessing.heap.BufferWrapper._heap
        heap._DISCARD_FREE_SPACE_LARGER_THAN = 0

        # create and destroy lots of blocks of different sizes
        for i in range(iterations):
            size = int(random.lognormvariate(0, 1) * 1000)
            b = multiprocessing.heap.BufferWrapper(size)
            blocks.append(b)
            if len(blocks) > maxblocks:
                i = random.randrange(maxblocks)
                del blocks[i]
            del b

        # verify the state of the heap
        with heap._lock:
            all = []
            free = 0
            occupied = 0
            for L in list(heap._len_to_seq.values()):
                # count all free blocks in arenas
                for arena, start, stop in L:
                    all.append((heap._arenas.index(arena), start, stop,
                                stop-start, 'free'))
                    free += (stop-start)
            for arena, arena_blocks in heap._allocated_blocks.items():
                # count all allocated blocks in arenas
                for start, stop in arena_blocks:
                    all.append((heap._arenas.index(arena), start, stop,
                                stop-start, 'occupied'))
                    occupied += (stop-start)

            self.assertEqual(free + occupied,
                             sum(arena.size for arena in heap._arenas))

            all.sort()

            for i in range(len(all)-1):
                (arena, start, stop) = all[i][:3]
                (narena, nstart, nstop) = all[i+1][:3]
                if arena != narena:
                    # Two different arenas
                    self.assertEqual(stop, heap._arenas[arena].size)  # last block
                    self.assertEqual(nstart, 0)         # first block
                else:
                    # Same arena: two adjacent blocks
                    self.assertEqual(stop, nstart)

        # test free'ing all blocks
        random.shuffle(blocks)
        while blocks:
            blocks.pop()

        self.assertEqual(heap._n_frees, heap._n_mallocs)
        self.assertEqual(len(heap._pending_free_blocks), 0)
        self.assertEqual(len(heap._arenas), 0)
        self.assertEqual(len(heap._allocated_blocks), 0, heap._allocated_blocks)
        self.assertEqual(len(heap._len_to_seq), 0)
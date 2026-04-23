def test_allgather_coalesced_async(self):
        store = c10d.FileStore(self.file_name, self.world_size)
        c10d.init_process_group(
            backend="gloo", rank=self.rank, world_size=self.world_size, store=store
        )

        xxs = [2 * [torch.tensor([i + self.rank])] for i in range(2)]
        yys = [
            [[torch.zeros_like(x) for x in xx] for _ in range(self.world_size)]
            for xx in xxs
        ]
        futs = [
            c10d.all_gather_coalesced(yy, xx, async_op=True) for xx, yy in zip(xxs, yys)
        ]

        # expected outputs
        zzs = [
            [2 * [torch.tensor([i + r])] for r in range(self.world_size)]
            for i in range(2)
        ]

        torch.futures.wait_all(futs)
        for yy, zz in zip(yys, zzs):
            # one iteration
            for y_out, z_out in zip(yy, zz):
                # one output tensor list
                for y, z in zip(y_out, z_out):
                    # one tensor in output tensor list
                    self.assertEqual(y, z)

        # Added to address https://github.com/pytorch/pytorch/issues/65231
        # In the failed tests, all assertEqual are passed on all processes.
        # However, one of the processes didn't call ProcessGroupGloo
        # destructor before exiting program. This is not surprising as the only
        # guarantee that Python makes is that garbage collection MAY happen
        # before the program exits. If GC didn't happen, the two threads in
        # ProcessGroup might be destructed before joined.
        # FIXME: it's still unclear why only this test require explicit
        # destroy_process_group()
        c10d.destroy_process_group()
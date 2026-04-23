def test_send_recv_all_to_all(self):
        store = c10d.FileStore(self.file_name, self.world_size)
        pg = self._create_process_group_gloo(
            store, self.rank, self.world_size, self.opts()
        )

        # Preallocate tensors for input/output
        inputs = [torch.tensor([self.rank]) for _ in range(self.world_size)]
        outputs = [torch.tensor([-1]) for _ in range(self.world_size)]

        # Issue sends
        send_work = []
        for i in range(self.world_size):
            if i == self.rank:
                continue
            send_work.append(pg.send([inputs[i]], i, 0))

        # Issue recvs
        recv_work = []
        for i in range(self.world_size):
            if i == self.rank:
                continue
            recv_work.append(pg.recv([outputs[i]], i, 0))

        # Wait for sends to complete
        for work in send_work:
            work.wait()
            self.assertTrue(work.is_completed())

        # Wait for recvs to complete
        for work in recv_work:
            work.wait()
            self.assertTrue(work.is_completed())

        # Test that every output other than our own contains the respective rank
        for i in range(self.world_size):
            if i == self.rank:
                continue
            self.assertEqual(torch.tensor([i]), outputs[i])
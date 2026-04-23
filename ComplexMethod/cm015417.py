def test_init_process_group_for_all_backends(self):
        for backend in dist.Backend.backend_list:
            excepted_backend = backend
            # skip if the backend is not available on the system
            if backend == dist.Backend.UNDEFINED:
                continue
            elif backend == dist.Backend.MPI:
                if not dist.is_mpi_available():
                    continue
            elif backend == dist.Backend.NCCL:
                if not dist.is_nccl_available() or not torch.cuda.is_available():
                    continue
            elif backend == dist.Backend.GLOO:
                if not dist.is_gloo_available():
                    continue
            elif backend == dist.Backend.UCC:
                if not dist.is_ucc_available():
                    continue
            elif backend == dist.Backend.XCCL:
                if not dist.is_xccl_available():
                    continue
            # Multi-threaded PG is defined as a pure python class.
            # Its pg.name() does not going through Pybind, so its backend name
            # is still "threaded" instead of "custom".
            elif backend != "threaded":
                excepted_backend = "custom"

            store = dist.FileStore(self.file_name, self.world_size)
            dist.init_process_group(
                backend=backend,
                rank=self.rank,
                world_size=self.world_size,
                store=store,
            )
            pg = c10d._get_default_group()
            self.assertEqual(pg.rank(), self.rank)
            self.assertEqual(pg.size(), self.world_size)
            self.assertEqual(pg.name(), str(excepted_backend))

            dist.destroy_process_group()
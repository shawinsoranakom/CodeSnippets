def _test_gather_object(self, pg=None):
            # Ensure stateful objects can be gathered
            gather_objects = create_collectives_object_test_list()
            my_rank = dist.get_rank(pg)

            backend = os.environ["BACKEND"]
            if backend == "nccl":
                # Case where rank != GPU device.
                next_rank = (self.rank + 1) % int(self.world_size)
                torch.cuda.set_device(next_rank)

            # If GPU test, add object with GPU tensor
            if backend == "nccl":
                gather_objects.append(Foo(torch.randn(3, 3, device=my_rank)))

            output_gathered = [None for _ in range(dist.get_world_size(pg))]
            gather_on_rank = 0
            dist.gather_object(
                gather_objects[self.rank % len(gather_objects)],
                object_gather_list=output_gathered
                if my_rank == gather_on_rank
                else None,
                dst=gather_on_rank,
                group=pg,
            )
            if my_rank != gather_on_rank:
                self.assertEqual(
                    output_gathered, [None for _ in range(dist.get_world_size())]
                )
            else:
                for i, val in enumerate(output_gathered):
                    expected = gather_objects[i % len(gather_objects)]
                    self.assertEqual(val, expected)

            # Validate errors when objects can't be pickled.
            class Bar:
                pass

            b = Bar()
            gather_objects = [b for _ in range(dist.get_world_size())]
            with self.assertRaises(AttributeError):
                dist.all_gather_object(
                    [None for _ in range(dist.get_world_size())],
                    gather_objects[self.rank],
                    group=pg,
                )
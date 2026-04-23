def _test_broadcast_object_list(self, group=None):
            gather_objects = create_collectives_object_test_list()

            # Only set device for NCCL backend since it must use GPUs.
            # Case where rank != GPU device.
            next_rank = (self.rank + 1) % int(self.world_size)
            backend = os.environ["BACKEND"]
            if backend == "nccl":
                torch.cuda.set_device(next_rank)

            src_rank = 0
            # If GPU test, add object with GPU tensor
            if backend == "nccl":
                gather_objects.append(Foo(torch.randn(3, 3, device=0)))

            if IS_FBCODE:
                # Create Tensor with > 2^31 Bytes storage requirements
                # Only on FBCODE as testing OOMs in OSS
                gather_objects.append(Foo(torch.randn(3, 178956971)))
            objects = (
                gather_objects
                if self.rank == src_rank
                else [None for _ in gather_objects]
            )

            # Single object test with device specified. Backend="gloo", device=cpu
            if backend != "nccl":
                single_obj_list = [objects[0]]
                if self.rank != src_rank:
                    self.assertNotEqual(single_obj_list[0], gather_objects[0])
                dist.broadcast_object_list(
                    single_obj_list, src=0, group=group, device=torch.device("cpu")
                )
                self.assertEqual(single_obj_list[0], gather_objects[0])

            # Single object test with device specified. Backend="gloo", device=current_device+1
            # The test is gated by the fact GPU count is the same as world size to avoid the case
            # when backend is gloo but there is no multiple GPU devices.
            if backend != "nccl" and torch.cuda.device_count() == int(self.world_size):
                single_obj_list = [objects[0]]
                if self.rank != src_rank:
                    self.assertNotEqual(single_obj_list[0], gather_objects[0])
                dist.broadcast_object_list(
                    single_obj_list, src=0, group=group, device=torch.device(next_rank)
                )
                self.assertEqual(single_obj_list[0], gather_objects[0])

            # Single object test with device specified. Backend="nccl", device=current_device+1
            if backend == "nccl" and torch.cuda.device_count() == int(self.world_size):
                single_obj_list = [objects[0]]
                if self.rank != src_rank:
                    self.assertNotEqual(single_obj_list[0], gather_objects[0])
                dist.broadcast_object_list(
                    single_obj_list, src=0, group=group, device=torch.device(next_rank)
                )
                self.assertEqual(single_obj_list[0], gather_objects[0])

            # Single object test: backward compatibility with device unspecified
            single_obj_list = [objects[0]]
            if self.rank != src_rank:
                self.assertNotEqual(single_obj_list[0], gather_objects[0])
            dist.broadcast_object_list(single_obj_list, src=0, group=group)
            self.assertEqual(single_obj_list[0], gather_objects[0])

            # Multiple input objects test
            if self.rank != src_rank:
                self.assertNotEqual(objects, gather_objects)
            dist.broadcast_object_list(objects, src=0, group=group)
            self.assertEqual(objects, gather_objects)
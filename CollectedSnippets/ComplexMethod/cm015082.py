def test_tensors_grouping(self):
        num_tensors_per_list = 10
        num_devices = torch.cuda.device_count()
        dtypes = (torch.float16, torch.float32, torch.float64)
        list1 = [
            torch.tensor(
                i,
                device=torch.device("cuda", random.randint(0, num_devices - 1)),
                dtype=dtypes[random.randint(0, 2)],
            )
            for i in range(num_tensors_per_list)
        ]
        list2 = [None for _ in list1]
        list3 = [torch.rand_like(t) for t in list1]
        nested_tensorlists = [list1, list2, list3]
        grouped_tensors = torch.utils._foreach_utils._group_tensors_by_device_and_dtype(
            nested_tensorlists, with_indices=True
        )
        num_tensors_seen = 0
        for (device, dtype), ([l1, l2, l3], indices) in grouped_tensors.items():
            for t in itertools.chain(l1, l3):
                self.assertEqual(t.device, device)
                self.assertEqual(t.dtype, dtype)
                num_tensors_seen += 1
            self.assertEqual(len(l1), len(l2))
            self.assertTrue(all(p is None for p in l2))
            for i, index in enumerate(indices):
                self.assertEqual(l1[i], list1[index])
                self.assertEqual(l2[i], list2[index])
                self.assertEqual(l3[i], list3[index])
        self.assertEqual(num_tensors_seen, 2 * num_tensors_per_list)
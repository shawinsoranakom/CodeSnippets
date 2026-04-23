def test_caching(self):
        """
        Test that the StateDictStager correctly caches and reuses storages.
        """
        test_configs = [
            (False, False),  # pin_memory=False, share_memory=False,
            (True, False),  # pin_memory=True, share_memory=False
            (False, True),  # pin_memory=False, share_memory=True
            (True, True),  # pin_memory=True, share_memory=True
        ]
        for pin_memory, share_memory in test_configs:
            with self.subTest(pin_memory=pin_memory, share_memory=share_memory):
                # Create test tensors and state dict
                tensor1 = torch.randn(4, 4).to(device_type)
                tensor2 = tensor1.view(16)
                tensor3 = torch.randn(4, 4).to(device_type)
                state_dict = {
                    "tensor1": tensor1,
                    "tensor2": tensor2,
                    "recursive": {
                        "tensor3": tensor3,
                        "type": TestStruct(tensor1=tensor3.narrow(0, 0, 2)),
                    },
                }

                # Create a StateDictStager instance
                stager = StateDictStager(
                    pin_memory=pin_memory, share_memory=share_memory
                )

                # First call to stage with staging context
                cpu_state_dict1 = stager.stage(state_dict)

                # Get the number of cached storages after first stage
                num_storages1 = len(stager._cached_storage_mapping)

                # Verify the first result is correct
                result, error = compare_state_dicts(state_dict, cpu_state_dict1)
                if not result:
                    raise AssertionError(
                        f"First state dict is not equivalent to original: {error}"
                    )

                # Modify the original tensors
                tensor1.fill_(0)
                tensor3.fill_(0)

                # Second call to stage with staging context
                cpu_state_dict2 = stager.stage(state_dict)

                # Get the number of cached storages after second stage
                num_storages2 = len(stager._cached_storage_mapping)

                # Verify that the second CPU state dict is equivalent to the modified original state dict
                result, error = compare_state_dicts(state_dict, cpu_state_dict2)
                if not result:
                    raise AssertionError(
                        f"Second state dict is not equivalent to modified original: {error}"
                    )

                # Verify that the number of cached storages hasn't changed
                if num_storages1 != num_storages2:
                    raise AssertionError(
                        f"Storage count changed: {num_storages1} vs {num_storages2}"
                    )

                # Verify that the tensors in the second state dict have the same storage pointers as the first
                if (
                    cpu_state_dict1["tensor1"].storage().data_ptr()
                    != cpu_state_dict2["tensor1"].storage().data_ptr()
                ):
                    raise AssertionError("Storage pointers should match for tensor1")
                if (
                    cpu_state_dict1["tensor2"].storage().data_ptr()
                    != cpu_state_dict2["tensor2"].storage().data_ptr()
                ):
                    raise AssertionError("Storage pointers should match for tensor2")
                if (
                    cpu_state_dict1["recursive"]["tensor3"].storage().data_ptr()
                    != cpu_state_dict2["recursive"]["tensor3"].storage().data_ptr()
                ):
                    raise AssertionError("Storage pointers should match for tensor3")

                # Modify the original tensors again with different values
                tensor1.fill_(42.0)

                # Third call to stage with staging context
                cpu_state_dict3 = stager.stage(state_dict)

                # Verify that the third CPU state dict reflects the updated values
                if not torch.all(cpu_state_dict3["tensor1"] == 42.0):
                    raise AssertionError(
                        "Updated values should be reflected in the cached state dict for tensor1"
                    )
                if not torch.all(cpu_state_dict3["tensor2"] == 42.0):
                    raise AssertionError(
                        "Updated values should be reflected in the cached state dict for tensor2"
                    )
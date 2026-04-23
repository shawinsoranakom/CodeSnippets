def test_views(self):
        test_configs = [
            (False, False),  # pin_memory=False, share_memory=False,
            (True, False),  # pin_memory=True, share_memory=False
            (False, True),  # pin_memory=False, share_memory=True
            (True, True),  # pin_memory=True, share_memory=True
        ]
        for pin_memory, share_memory in test_configs:
            with self.subTest(pin_memory=pin_memory, share_memory=share_memory):
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
                if (
                    state_dict["tensor1"].storage().data_ptr()
                    != state_dict["tensor2"].storage().data_ptr()
                ):
                    raise AssertionError("tensor1 and tensor2 should share storage")

                stager = StateDictStager(
                    pin_memory=pin_memory, share_memory=share_memory
                )

                cpu_state_dict = stager.stage(state_dict)

                # Calculate stats
                num_storages = len(stager._cached_storage_mapping)
                num_bytes = sum(
                    storage.nbytes()
                    for storage in stager._cached_storage_mapping.values()
                )

                # Validate tensor count and bytes
                expected_storage_cnt = 2
                if num_storages != expected_storage_cnt:
                    raise AssertionError(
                        f"Expected {expected_storage_cnt} storages, got {num_storages}"
                    )

                # Calculate expected bytes
                # Note: Only unique storages are counted in the byte count
                expected_bytes = (
                    tensor1.numel() * tensor1.element_size()
                    + tensor3.numel()  # tensor1 and tensor2 share storage
                    * tensor3.element_size()  # tensor3 and its narrow view share storage
                )
                if num_bytes != expected_bytes:
                    raise AssertionError(
                        f"Expected {expected_bytes} bytes, got {num_bytes}"
                    )
                # Verify that the CPU state dict is equivalent to the original GPU state dict
                result, error = compare_state_dicts(state_dict, cpu_state_dict)
                if not result:
                    raise AssertionError(f"State dicts are not equivalent: {error}")

                # Additional checks for storage sharing
                if cpu_state_dict["tensor1"].device != torch.device("cpu"):
                    raise AssertionError(
                        f"Expected tensor1 on cpu, got {cpu_state_dict['tensor1'].device}"
                    )
                if cpu_state_dict["tensor2"].device != torch.device("cpu"):
                    raise AssertionError(
                        f"Expected tensor2 on cpu, got {cpu_state_dict['tensor2'].device}"
                    )
                if (
                    cpu_state_dict["tensor1"].storage().data_ptr()
                    != cpu_state_dict["tensor2"].storage().data_ptr()
                ):
                    raise AssertionError("cpu tensor1 and tensor2 should share storage")

                recursive = cpu_state_dict["recursive"]
                if recursive["tensor3"].device != torch.device("cpu"):
                    raise AssertionError(
                        f"Expected tensor3 on cpu, got {recursive['tensor3'].device}"
                    )
                if recursive["type"].tensor1.device != torch.device("cpu"):
                    raise AssertionError(
                        f"Expected type.tensor1 on cpu, got {recursive['type'].tensor1.device}"
                    )
                if (
                    recursive["tensor3"].storage().data_ptr()
                    != recursive["type"].tensor1.storage().data_ptr()
                ):
                    raise AssertionError(
                        "tensor3 and type.tensor1 should share storage"
                    )
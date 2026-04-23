def test_generate_shard_orders(self):
        """Check if `generate_shard_orders` generates unique sharding combinations"""
        import math

        test_inputs = [
            {"mesh": init_device_mesh(self.device_type, (2, 2, 2)), "tensor_rank": 2},
            {"mesh": init_device_mesh(self.device_type, (2, 2, 2)), "tensor_rank": 3},
            {"mesh": init_device_mesh(self.device_type, (2, 2, 2)), "tensor_rank": 4},
        ]
        for test_input in test_inputs:
            all_combinations = []
            for shard_order in generate_shard_orders(
                test_input["mesh"], test_input["tensor_rank"]
            ):
                all_combinations.append(shard_order)  # noqa: PERF402
            for i in range(len(all_combinations)):
                for j in range(i + 1, len(all_combinations)):
                    if all_combinations[i] == all_combinations[j]:
                        raise AssertionError(
                            f"Duplicate elements found in all_combinations {all_combinations[i]}, {all_combinations[j]}"
                        )
            expected_total_combination = 0
            N = test_input["mesh"].ndim
            M = test_input["tensor_rank"]
            for i in range(1, N + 1):
                # assign total i split of device to tensor dims
                if M < i:
                    continue
                device_combination_count = math.comb(
                    N - 1, i - 1
                )  # choose i-1 non-empty segments from a list of size N
                tensor_dim_order_permutation = math.comb(M, i)  # choose i tensor dims
                expected_total_combination += (
                    device_combination_count * tensor_dim_order_permutation
                )
            # multiply by total possible permutation of device order
            expected_total_combination *= math.factorial(N)
            self.assertEqual(len(all_combinations), expected_total_combination)
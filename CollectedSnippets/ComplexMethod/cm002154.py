def sanity_check_tensor_sync(
    tensor: torch.Tensor, mesh: DeviceMesh, rtol: float = 1e-4, atol: float = 1e-4, not_sync: bool = False
) -> None:
    """
    Verify that a tensor is synchronized (or not synchronized) across all processes in the mesh's process group.
    Handles both regular tensors and DTensors.

    Args:
        tensor (torch.Tensor): The tensor to check for synchronization (can be DTensor)
        mesh (DeviceMesh): The device mesh containing the process group
        rtol (float): Relative tolerance for comparison
        atol (float): Absolute tolerance for comparison
        not_sync (bool): If True, asserts that tensors are NOT synchronized. If False, asserts they are synchronized.
    """
    if not dist.is_initialized() or mesh.size() == 1:
        return  # No need to check in non-distributed mode

    # Get the process group from the mesh
    pg = mesh.get_group()

    # Convert DTensor to local tensor if needed
    if hasattr(tensor, "to_local"):
        local_tensor = tensor.to_local()
    else:
        local_tensor = tensor

    # Gather tensors from all processes
    world_size = dist.get_world_size(pg)
    gathered_tensors = [torch.empty_like(local_tensor) for _ in range(world_size)]
    dist.all_gather(gathered_tensors, local_tensor, group=pg)

    # Compare each tensor with the first one
    for i in range(1, world_size):
        try:
            torch.testing.assert_close(gathered_tensors[0], gathered_tensors[i], rtol=rtol, atol=atol)
        except AssertionError as e:
            if not_sync:
                continue
            # # Add detailed debugging for logit synchronization issues
            # print(f"\nLogit synchronization error between rank 0 and rank {i}:")
            # print(f"Tensor shape: {gathered_tensors[0].shape}")
            # print(f"Number of mismatched elements: {(gathered_tensors[0] != gathered_tensors[i]).sum()}")
            # print(f"Percentage of mismatched elements: {((gathered_tensors[0] != gathered_tensors[i]).sum() / gathered_tensors[0].numel() * 100):.2f}%")

            # # Find the first few mismatches
            # mismatches = torch.nonzero(gathered_tensors[0] != gathered_tensors[i])
            # print("\nFirst few mismatches:")
            # for idx in mismatches[:5]:
            #     idx = tuple(idx.tolist())
            #     print(f"Index {idx}:")
            #     print(f"Rank 0 value: {gathered_tensors[0][idx]}")
            #     print(f"Rank {i} value: {gathered_tensors[i][idx]}")
            #     print(f"Absolute difference: {abs(gathered_tensors[0][idx] - gathered_tensors[i][idx])}")
            #     print(f"Relative difference: {abs(gathered_tensors[0][idx] - gathered_tensors[i][idx]) / max(abs(gathered_tensors[0][idx]), abs(gathered_tensors[i][idx]))}")

            # # Check if differences are systematic (e.g., all positive or negative)
            # diff = gathered_tensors[0] - gathered_tensors[i]
            # print(f"\nDifference statistics:")
            # print(f"Mean difference: {diff.mean()}")
            # print(f"Std difference: {diff.std()}")
            # print(f"Max positive difference: {diff.max()}")
            # print(f"Max negative difference: {diff.min()}")
            raise e
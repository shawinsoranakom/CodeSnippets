def reduce_tensor(tensor):
    if tensor.requires_grad and not tensor.is_leaf:
        raise RuntimeError(
            "Cowardly refusing to serialize non-leaf tensor which requires_grad, "
            "since autograd does not support crossing process boundaries.  "
            "If you just want to transfer the data, call detach() on the tensor "
            "before serializing (e.g., putting it on the queue)."
        )

    check_serializing_named_tensor(tensor)
    torch.utils.hooks.warn_if_has_hooks(tensor)

    # Note [CUDA IPC and the caching allocator]
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # When you send a CUDA tensor over IPC, you might expect that you will
    # get out the same storage from the other end.  However, the CUDA caching
    # allocator makes it difficult to preserve this invariant.  Consider
    # the following situation: a tensor of size 0x100 points to offset 0x20 of
    # a storage at 0xA100 of size 0x100.  (For simplicity, all of these
    # sizes are given in bytes).  HOWEVER, with the caching allocator, this storage
    # might be part of a larger cudaMalloc allocation 0xA000 of size 0x4000.
    #
    # When we want to send this CUDA tensor over IPC, we must send the
    # *entire* cudaMalloc allocation, i.e., the 0xA000 region, not just
    # the storage 0xA100 (because that is what CUDA supports).  So, on the
    # other end, there simply isn't any way to say, "Wait, you gave me
    # a bigger region (0xA000) than the one I wanted (0xA100)".
    #
    # OK, so if you sent the cudaMalloc allocation, can you just wrap that up as
    # one storage itself? No, because this cudaMalloc allocation might contain
    # storages of mixed types: float, bytes, double... If you make the entire
    # allocation a single storage of a type A, we'll hit an error when constructing
    # a tensor of type B on the storage.
    #
    # cudaIpcMemHandle is an identifier to access the sender cudaMalloc allocation on the
    # receiver side. However, cudaIpcMemHandles from each device in a given process may
    # only be opened by one context per device per other process.
    # If we open and close a memory handle multiples times in a process, CUDA is allowed
    # to give it a different address; similarly, once we close the memory, we're not
    # allowed to access it(and the storage/tensor built on top of it), even if it is
    # still live in the original process. As we cannot make a cudaMalloc allocation
    # to a single storage in one go, this requires us to cache the device pointer for
    # each cudaIpcMemHandle on C++ side to reconstruct types of storages, while keep
    # the old ones alives.
    # See [https://docs.nvidia.com/cuda/cuda-runtime-api/group__CUDART__DEVICE.html]
    #
    # This is fine, because all we need to do is to save our position in the allocation,
    # and reconstruct storage and tensor from it.
    # 0xA000 ->  -------CUDA Allocation------
    #           |                            |
    #           |                            |
    #           |                            |
    #           |                            |
    # 0xA100 ->  --------storage1 begin------
    #           |                            |
    # 0xA120 ->  --------tensor1 begin ------
    #           |                            |
    #           |                            |
    #           |                            |
    #           |                            |
    #           |                            |
    # 0xA160 ->  --------tensor1 end---------
    #           |                            |
    #           |                            |
    #           |                            |
    # 0xA200 ->  --------storage1 end--------
    #           |                            |
    # 0xE000 ->  --------CUDA allocation-----
    #
    # To send tensor1, the following info are required from sender to receiver for
    # storage reconstruction.
    #   1. cudaIpcMemHandle of 0xA000(which can be mapped to a basePtr in receiver process).
    #      basePtr may not be exactly 0xA000 since it's a different process.
    #   2. offset(0xA100) of storage1 in the CUDA allocation.
    #   3. size of storage1(0x100).
    #
    # On receiver side:
    #   1. Get the devPtr of the MemHandle to access the memory, reconstruct a storage
    #      of the same type using (basePtr, offset, size).
    #   2. we can reconstruct the tensor on top of the reconstructed storage
    #   Tensor(size=0x040, offset=0x020, storage=Storage(data=basePtr+0xA100, size=0x0100))
    #
    # This strategy has a few implications:
    #
    # 1. When we serialize a CUDA tensor for IPC, we cannot do it all in one
    #    go (non-compositionally), and this requires to have a global map
    #    memHandle -> devPtr for each process.
    #
    # 2. We MUST NOT let the new IPC tensor be resizable.  Originally, a resize
    #    of the storage beyond 0x100 would merely have caused us to do a
    #    reallocation.  You don't really want to do this, but if you did,
    #    all that would happen is that you would lose IPC sharing.  But if
    #    you do this in the new world, we will happily let you write out of
    #    bounds of your "allocation", clobbering unrelated data in the cached
    #    allocator block.  BAD!
    #
    # By the way, in old versions of PyTorch, we supported this situation
    # natively using a "storage view", which permitted multiple storages to be
    # views on each other.  But this was the *only* use of storage views, so we
    # eliminated it so that we could just use tensor views to implement the same
    # thing.
    #

    # TODO: Handle distinguishing between subclass and non-subclass versions of NT better
    # https://github.com/pytorch/pytorch/issues/110543
    from torch.nested._internal.nested_tensor import NestedTensor

    if tensor.is_nested and not isinstance(tensor, NestedTensor):
        return reduce_nested_tensor(tensor)

    if tensor.layout in {
        torch.sparse_coo,
        torch.sparse_csr,
        torch.sparse_bsr,
        torch.sparse_csc,
        torch.sparse_bsc,
    }:
        return reduce_sparse_tensor(tensor)

    storage = tensor._typed_storage()

    if storage._untyped_storage.device.type == "cuda":
        (
            device,
            handle,
            storage_size_bytes,
            storage_offset_bytes,
            ref_counter_handle,
            ref_counter_offset,
            event_handle,
            event_sync_required,
        ) = storage._share_cuda_()
        tensor_offset = tensor.storage_offset()
        shared_cache[handle] = StorageWeakRef(storage)
        # _backward_hooks purposely omitted here, see
        # Note [Don't serialize hooks]
        return (
            rebuild_cuda_tensor,
            (
                type(tensor),
                tensor.size(),
                tensor.stride(),
                tensor_offset,  # tensor offset in its storage
                type(storage),
                tensor.dtype,
                device,
                handle,  # identifier which CUDA allocation is the storage in.
                storage_size_bytes,  # size(in bytes) of the storage
                storage_offset_bytes,  # offset(in bytes) of the storage in the CUDA allocation
                tensor.requires_grad,
                ref_counter_handle,
                ref_counter_offset,
                event_handle,
                event_sync_required,
            ),
        )
    elif storage._untyped_storage.device.type == "meta":
        return (
            rebuild_meta_tensor,
            (
                type(tensor),
                tensor.size(),
                tensor.stride(),
                tensor.storage_offset(),
                tensor.dtype,
                tensor.untyped_storage().size(),
                tensor.requires_grad,
            ),
        )

    # _backward_hooks purposely omitted here, see Note [Don't serialize hooks]
    metadata = (
        tensor.storage_offset(),
        tensor.size(),
        tensor.stride(),
        tensor.requires_grad,
    )
    return (rebuild_tensor, (type(tensor), storage, metadata))
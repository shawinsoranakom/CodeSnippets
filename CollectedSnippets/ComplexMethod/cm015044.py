def _generate_invalid_input(self, layout, device):
        from functools import partial

        def shape(shape, basedim=0):
            blocksize = (1, 1)
            if layout is torch.sparse_csc:
                shape = shape[:basedim] + (shape[basedim + 1], shape[basedim]) + shape[basedim + 2:]
            elif layout is torch.sparse_bsc:
                shape = shape[:basedim] + (shape[basedim + 1] * blocksize[1], shape[basedim] * blocksize[0]) + shape[basedim + 2:]
            elif layout is torch.sparse_bsr:
                shape = shape[:basedim] + (shape[basedim] * blocksize[0], shape[basedim + 1] * blocksize[1]) + shape[basedim + 2:]
            return shape

        def values(lst, device=device):
            if layout in {torch.sparse_bsr, torch.sparse_bsc}:
                lst = [[[item]] for item in lst]
            return torch.tensor(lst, device=device)

        tensor = partial(torch.tensor, device=device)
        values = partial(values, device=device)

        yield ('incontiguous compressed_indices',
               tensor([0, -1, 2, -1, 4, -1])[::2],
               tensor([0, 1, 0, 2]),
               values([1, 2, 3, 4]),
               shape((2, 3)),
               'expected compressed_indices to be a contiguous tensor per batch')

        yield ('incontiguous plain_indices',
               tensor([0, 2, 4]),
               tensor([0, -1, 1, -1, 0, -1, 2, -1])[::2],
               values([1, 2, 3, 4]),
               shape((2, 3)),
               'expected plain_indices to be a contiguous tensor per batch')

        yield ('0-D compressed_indices',
               tensor(0),
               tensor([0, 1, 0, 2]),
               values([1, 2, 3, 4]),
               shape((2, 3)),
               'compressed_indices must have dimensionality >= 1 but got 0')

        yield ('compressed/plain_indices mismatch of dimensionalities',
               tensor([[0, 2, 4]]),
               tensor([0, 1, 0, 2]),
               values([1, 2, 3, 4]),
               shape((2, 3)),
               'compressed_indices and plain_indices dimensionalities must be equal but got 2 and 1, respectively')

        if layout in {torch.sparse_csr, torch.sparse_csc}:
            yield ('indices and values mismatch of dimensionalities',
                   tensor([[0, 2, 4]]),
                   tensor([[0, 1, 0, 2]]),
                   values([1, 2, 3, 4]),
                   shape((2, 3)),
                   r'values must have dimensionality > sum of batch and block dimensionalities \(=1 \+ 0\) but got 1')
        else:
            yield ('indices and values mismatch of dimensionalities',
                   tensor([[0, 2, 4]]),
                   tensor([[0, 1, 0, 2]]),
                   values([1, 2, 3, 4]),
                   shape((2, 3)),
                   r'values must have dimensionality > sum of batch and block dimensionalities \(=1 \+ 2\) but got 3')

        yield ('invalid size',
               tensor([0, 2, 4]),
               tensor([0, 1, 0, 2]),
               values([1, 2, 3, 4]),
               (2,),
               r'tensor dimensionality must be sum of batch, base, and dense dimensionalities \(=0 \+ 2 \+ 0\) but got 1')

        yield ('invalid batchsize',
               tensor([[0, 2, 4]]),
               tensor([[0, 1, 0, 2]]),
               values([[1, 2, 3, 4]]),
               shape((2, 2, 3), 1),
               r'all batch dimensions of compressed_indices \(=\[1\]\), plain_indices \(=\[1\]\), '
               r'and values \(=\[1\]\) must be equal to tensor batch dimensions \(=\[2\]\)')

        if layout is torch.sparse_bsr:
            yield ('invalid blocksize',
                   tensor([0, 2, 4]),
                   tensor([0, 1, 0, 2]),
                   tensor([[[1, 11]], [[2, 22]], [[3, 33]], [[4, 33]]]),
                   shape((2, 3)),
                   r'tensor shape\[1\] \(=3\) must be divisible with blocksize\[1\] \(=2\) as defined by values shape')

        if layout is torch.sparse_bsc:
            yield ('invalid blocksize',
                   tensor([0, 2, 4]),
                   tensor([0, 1, 0, 2]),
                   tensor([[[1, 11]], [[2, 22]], [[3, 33]], [[4, 33]]]),
                   shape((3, 2)),
                   r'tensor shape\[1\] \(=3\) must be divisible with blocksize\[1\] \(=2\) as defined by values shape')

        yield ('invalid compressed_indices shape',
               tensor([0, 2, 3, 4]),
               tensor([0, 1, 0, 2]),
               values([1, 2, 3, 4]),
               shape((2, 3)),
               r'compressed_indices.shape\[-1\] must be equal to the number of compressed_indices_names \+ 1 \(=3\), but got 4')

        yield ('invalid compressed_indices shape',
               tensor([0, 2, 4]),
               tensor([0, 1, 0, 1, 2]),
               values([1, 2, 3, 4]),
               shape((2, 3)),
               r'plain_indices.shape\[-1\] must be equal to nnz \(=4\) as defined by values.shape\[0\], but got 5')

        yield ('compressed/plain_indices mismatch of dtype',
               tensor([0, 2, 4], dtype=torch.int32),
               tensor([0, 1, 0, 2], dtype=torch.int64),
               values([1, 2, 3, 4]),
               shape((2, 3)),
               r'compressed_indices and plain_indices must have the same dtype, bot got Int and Long, respectively')

        yield ('invalid compressed/plain_indices dtype',
               tensor([0, 2, 4], dtype=torch.int16),
               tensor([0, 1, 0, 2], dtype=torch.int16),
               values([1, 2, 3, 4]),
               shape((2, 3)),
               r'compressed_indices and plain_indices dtype must be Int or Long, but got Short')

        # CUDA kernel asserts are not recoverable, so we skip these for now
        if torch.device(device).type == 'cpu':
            yield ('invalid compressed_indices[0]',
                   tensor([1, 2, 4]),
                   tensor([0, 1, 0, 2]),
                   values([1, 2, 3, 4]),
                   shape((2, 3)),
                   r'`compressed_indices\[..., 0\] == 0` is not satisfied.')

            yield ('invalid compressed_indices[0] when nnz == 0',
                   tensor([1, 0], dtype=torch.int64),
                   tensor([], dtype=torch.int64),
                   values([1])[:0],
                   shape((1, 1)),
                   r'`compressed_indices\[..., 0\] == 0` is not satisfied.')

            yield ('invalid compressed_indices[-1]',
                   tensor([0, 2, 5]),
                   tensor([0, 1, 0, 2]),
                   values([1, 2, 3, 4]),
                   shape((2, 3)),
                   r'`compressed_indices\[..., -1\] == nnz` is not satisfied.')

            yield ('invalid compressed_indices[-1] when nnz == 0',
                   tensor([0, 1], dtype=torch.int64),
                   tensor([], dtype=torch.int64),
                   values([1])[:0],
                   shape((1, 1)),
                   r'`compressed_indices\[..., -1\] == nnz` is not satisfied.')

            yield ('invalid compressed_indices.diff(dim=-1)',
                   tensor([0, 0, 4]),
                   tensor([0, 1, 0, 2]),
                   values([1, 2, 3, 4]),
                   shape((2, 3)),
                   r'0 <= compressed_indices\[..., 1:\] - compressed_indices\[..., :\-1\] <= plain_dim` is not satisfied.')

            yield ('invalid compressed_indices.diff(dim=-1)',
                   tensor([0, 5, 4]),
                   tensor([0, 1, 0, 2]),
                   values([1, 2, 3, 4]),
                   shape((2, 3)),
                   r'0 <= compressed_indices\[..., 1:\] - compressed_indices\[..., :\-1\] <= plain_dim` is not satisfied.')

            yield ('invalid min(plain_indices)',
                   tensor([0, 2, 4]),
                   tensor([0, -1, 0, 3]),
                   values([1, 2, 3, 4]),
                   shape((2, 3)),
                   r'`0 <= plain_indices < plain_dim` is not satisfied.')

            yield ('invalid max(plain_indices)',
                   tensor([0, 2, 4]),
                   tensor([0, 1, 0, 3]),
                   values([1, 2, 3, 4]),
                   shape((2, 3)),
                   r'`0 <= plain_indices < plain_dim` is not satisfied.')

            yield ('non-coalesced',
                   tensor([0, 2, 4]),
                   tensor([1, 0, 0, 2]),
                   values([1, 2, 3, 4]),
                   shape((2, 3)),
                   r'`plain_indices\[..., compressed_indices\[..., i - 1\]:compressed_indices\[..., i\]\] '
                   'for all i = 1, ..., compressed_dim '
                   'are sorted and distinct along the last dimension values` is not satisfied.')

        if TEST_CUDA and torch.device(device).type == 'cpu':
            yield ('indices and values mismatch of device',
                   torch.tensor([0, 2, 4]),
                   torch.tensor([0, 1, 0, 1]),
                   values([1, 2, 3, 4], device='cuda'),
                   shape((2, 3)),
                   r'device of compressed_indices \(=cpu\) must match device of values \(=cuda:0\)')
            yield ('compressed_indices and values mismatch of device',
                   torch.tensor([0, 2, 4], device='cuda'),
                   torch.tensor([0, 1, 0, 1]),
                   values([1, 2, 3, 4]),
                   shape((2, 3)),
                   r'Expected all tensors to be on the same device, but found at least two devices, cuda:0 and cpu!')
            yield ('compressed/plain_indices mismatch of device',
                   torch.tensor([0, 2, 4], device='cuda'),
                   torch.tensor([0, 1, 0, 1]),
                   values([1, 2, 3, 4], device='cuda'),
                   shape((2, 3)),
                   r'Expected all tensors to be on the same device, but found at least two devices, cuda:0 and cpu!')

        if TEST_CUDA and torch.device(device).type == 'cuda' and torch.cuda.device_count() >= 2:
            yield ('indices and values mismatch of device index',
                   torch.tensor([0, 2, 4], device='cuda:0'),
                   torch.tensor([0, 1, 0, 1], device='cuda:0'),
                   values([1, 2, 3, 4], device='cuda:1'),
                   shape((2, 3)),
                   r'device of compressed_indices \(=cuda:0\) must match device of values \(=cuda:1\)')
            yield ('compressed_indices and values mismatch of device index',
                   torch.tensor([0, 2, 4], device='cuda:0'),
                   torch.tensor([0, 1, 0, 1], device='cuda:1'),
                   values([1, 2, 3, 4], device='cuda:0'),
                   shape((2, 3)),
                   r'Expected all tensors to be on the same device, but found at least two devices, cuda:0 and cuda:1!')
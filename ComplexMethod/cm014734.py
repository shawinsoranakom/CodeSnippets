def test_grid_sample(self):
        # Backward pass of native C++ and CUDA kernels branch depending on whether input requires gradient,
        # so we test both cases.
        def test(N, C, H, W, mode, padding_mode, align_corners, input_requires_grad):
            def test_shape(N, C, IH, IW, H, W, mode, padding_mode, align_corners):
                for grid_dim_contig_order in [(0, 1, 2, 3), (0, 3, 1, 2), (3, 0, 1, 2), (0, 2, 1, 3)]:
                    # grid_dim_contig_order specifies the dimension order that can
                    # make grid to be contiguous.
                    # i.e., grid.permute(grid_dim_contig_order) is contiguous.
                    # e.g., with grid_dim_contig_order=[0, 3, 1, 2], grid should be
                    #       initialized with contiguous tensor of shape [N, 2, H, W]
                    #       and permuted to [N, H, W, 2] afterwards.
                    grid_shape = [N, H, W, 2]
                    grid_init_shape = [grid_shape[d] for d in grid_dim_contig_order]
                    grid_fwd_permute = [None, None, None, None]
                    for i, d in enumerate(grid_dim_contig_order):
                        grid_fwd_permute[d] = i

                    def get_grid(device='cpu', data=None):
                        if data is not None:
                            if list(data.shape) != grid_shape:
                                raise AssertionError(f"data.shape mismatch: {list(data.shape)} != {grid_shape}")
                            data = data.permute(grid_dim_contig_order).to(device)
                        else:
                            data = torch.randn(grid_init_shape, device=device)
                        grid = data.permute(grid_fwd_permute)
                        if not grid.permute(grid_dim_contig_order).is_contiguous():
                            raise AssertionError("expected grid to be contiguous after permute")
                        return grid

                    input_cpu = torch.randn(C, N, IH, IW).transpose(0, 1).requires_grad_(input_requires_grad)
                    grid_cpu = get_grid().requires_grad_()
                    out_cpu = F.grid_sample(input_cpu, grid_cpu, mode=mode, padding_mode=padding_mode,
                                            align_corners=align_corners)
                    self.assertTrue(out_cpu.size() == torch.Size([N, C, H, W]))

                    gradients = torch.randn_like(out_cpu)
                    out_cpu.backward(gradients)


                    # Compare against unvectorized CPU fallback

                    # NOTE [ grid_sample CPU fallback ]
                    # grid_sample uses AVX for 2d images, but that requires 32-bit indexing for
                    # 32-bit floats. So we also have a fallback that is used only for float tensors
                    # requiring 64-bit indexing. That requires too much memory to run on CI, so we
                    # also export the fallback and test it here to ensure feature parity with
                    # the vectorized version.
                    input_fallback = input_cpu.float().detach_().requires_grad_()
                    grid_fallback = grid_cpu.float().detach_().requires_grad_()
                    out_fallback = torch._grid_sampler_2d_cpu_fallback(
                        input_fallback, grid_fallback,
                        F.GRID_SAMPLE_INTERPOLATION_MODES[mode],
                        F.GRID_SAMPLE_PADDING_MODES[padding_mode],
                        align_corners)
                    self.assertEqual(out_fallback, out_cpu.float(), atol=1e-5, rtol=5e-5)

                    out_fallback.backward(gradients.float())
                    if input_requires_grad:
                        self.assertEqual(input_fallback.grad, input_cpu.grad.float(), atol=1e-4, rtol=5e-5)
                    self.assertEqual(grid_fallback.grad, grid_cpu.grad.float(), atol=1e-4, rtol=5e-5)

                    if TEST_CUDA:
                        input_cuda = input_cpu.detach().transpose(0, 1).cuda().transpose(0, 1).requires_grad_(input_requires_grad)
                        grid_cuda = get_grid('cuda', grid_cpu.detach()).requires_grad_()
                        out_cuda = F.grid_sample(input_cuda, grid_cuda, mode=mode, padding_mode=padding_mode,
                                                 align_corners=align_corners)
                        self.assertEqual(out_cpu, out_cuda)

                        out_cuda.backward(gradients.cuda())
                        if input_requires_grad:
                            self.assertEqual(input_cpu.grad, input_cuda.grad)
                        self.assertEqual(grid_cpu.grad, grid_cuda.grad, atol=5e-5, rtol=0)

                        # check that zero-dimensional input strides don't error out
                        base_input = torch.randn(N, C, 1, IW)
                        input_cpu = base_input.expand_as(input_cuda).requires_grad_(input_requires_grad)
                        out_cpu = F.grid_sample(input_cpu, grid_cpu, mode=mode, padding_mode=padding_mode,
                                                align_corners=align_corners)

                        input_cuda = base_input.cuda().expand_as(input_cuda).requires_grad_(input_requires_grad)
                        out_cuda = F.grid_sample(input_cuda, grid_cuda, mode=mode, padding_mode=padding_mode,
                                                 align_corners=align_corners)
                        self.assertEqual(out_cpu, out_cuda)

            # test same size output
            test_shape(N, C, H, W, H, W, mode, padding_mode, align_corners)

            # test larger output
            N = random.randint(2, 8)
            C = random.randint(2, 8)
            IH = random.randint(2, 8)
            IW = random.randint(2, 8)
            H = random.randint(IH + 1, 12)
            W = random.randint(IW + 1, 12)
            test_shape(N, C, IH, IW, H, W, mode, padding_mode, align_corners)

            # test smaller output
            N = random.randint(2, 8)
            C = random.randint(2, 8)
            IH = random.randint(2, 8)
            IW = random.randint(2, 8)
            H = random.randint(2, IH)
            W = random.randint(2, IW)
            test_shape(N, C, IH, IW, H, W, mode, padding_mode, align_corners)

            # test 1x1 inpput
            N = random.randint(2, 8)
            C = random.randint(2, 8)
            IH = 1
            IW = 1
            H = random.randint(2, 5)
            W = random.randint(2, 5)
            test_shape(N, C, IH, IW, H, W, mode, padding_mode, align_corners)

            # testing empty grid
            N = random.randint(2, 8)
            C = random.randint(2, 8)
            IH = random.randint(2, 8)
            IW = random.randint(2, 8)
            W = random.randint(3, IW + 2)
            test_shape(N, C, IH, IW, 0, W, mode, padding_mode, align_corners)

            # testing empty channel
            N = random.randint(2, 8)
            IH = random.randint(2, 8)
            IW = random.randint(2, 8)
            H = random.randint(3, IH + 2)
            W = random.randint(3, IW + 2)
            test_shape(N, 0, IH, IW, H, W, mode, padding_mode, align_corners)

            # testing empty batch
            C = random.randint(2, 8)
            IH = random.randint(2, 8)
            IW = random.randint(2, 8)
            H = random.randint(3, IH + 2)
            W = random.randint(3, IW + 2)
            test_shape(0, C, IH, IW, H, W, mode, padding_mode, align_corners)

        for mode in ('bilinear', 'nearest', 'bicubic'):
            for padding_mode in ('zeros', 'border', 'reflection'):
                for align_corners in (True, False):
                    # test known input on CPU
                    input = torch.arange(1., 11).view(1, 1, 2, 5)
                    grid = torch.tensor(
                        [[[-0.9, -4.1], [0, 0.2000], [1, -1], [-0.333, 1e-6], [0.5, 1.0]],
                         [[-1.0, -0.5], [0, 0.3333], [1, -1], [-0.200, 1e-6], [1.5, 0.5]]]).view(1, 2, 5, 2)
                    if mode == 'bilinear':
                        if padding_mode == 'zeros':
                            if align_corners:
                                groundtruth = torch.tensor(
                                    [[0.0000, 6.0000000000, 5.0000, 4.8340, 9.0000],
                                     [2.2500, 6.3332500450, 5.0000, 5.1000, 0.0000]]).view(1, 1, 2, 5)
                            else:
                                groundtruth = torch.tensor(
                                    [[0.0000, 6.5000000000, 1.2500, 4.6675000191, 4.6250],
                                     [0.5000, 7.1665000916, 1.2500, 5.0000000000, 0.0000]]).view(1, 1, 2, 5)
                        elif padding_mode == 'border':
                            if align_corners:
                                groundtruth = torch.tensor(
                                    [[1.2000, 6.0000000000, 5.0000, 4.8340, 9.0000],
                                     [2.2500, 6.3332500450, 5.0000, 5.1000, 8.7500]]).view(1, 1, 2, 5)
                            else:
                                groundtruth = torch.tensor(
                                    [[1.0000, 6.5000000000, 5.0000, 4.6675000191, 9.2500],
                                     [1.0000, 7.1665000916, 5.0000, 5.0000000000, 10.0000]]).view(1, 1, 2, 5)
                        elif padding_mode == 'reflection':
                            if align_corners:
                                groundtruth = torch.tensor(
                                    [[3.4500, 6.0000000000, 5.0000, 4.8340, 9.0000],
                                     [2.2500, 6.3332500450, 5.0000, 5.1000, 7.7500]]).view(1, 1, 2, 5)
                            else:
                                groundtruth = torch.tensor(
                                    [[3.0000004768, 6.5000000000, 5.0000, 4.6675000191, 9.2500],
                                     [1.0000000000, 7.1665000916, 5.0000, 5.0000000000, 9.2500]]).view(1, 1, 2, 5)
                        else:
                            raise AssertionError(f"missing groundtruth test for padding mode '{padding_mode}'")
                    elif mode == 'nearest':
                        if padding_mode == 'zeros':
                            if align_corners:
                                groundtruth = torch.tensor(
                                    [[0., 8., 5., 7., 9.],
                                     [1., 8., 5., 8., 0.]]).view(1, 1, 2, 5)
                            else:
                                groundtruth = torch.tensor(
                                    [[0., 8., 5., 7., 0.],
                                     [1., 8., 5., 8., 0.]]).view(1, 1, 2, 5)
                        elif padding_mode == 'border':
                            if align_corners:
                                groundtruth = torch.tensor(
                                    [[1., 8., 5., 7., 9.],
                                     [1., 8., 5., 8., 10.]]).view(1, 1, 2, 5)
                            else:
                                groundtruth = torch.tensor(
                                    [[1., 8., 5., 7., 9.],
                                     [1., 8., 5., 8., 10.]]).view(1, 1, 2, 5)
                        elif padding_mode == 'reflection':
                            if align_corners:
                                groundtruth = torch.tensor(
                                    [[1., 8., 5., 7., 9.],
                                     [1., 8., 5., 8., 9.]]).view(1, 1, 2, 5)
                            else:
                                groundtruth = torch.tensor(
                                    [[1., 8., 5., 7., 9.],
                                     [1., 8., 5., 8., 9.]]).view(1, 1, 2, 5)
                        else:
                            raise AssertionError(f"missing groundtruth test for padding mode '{padding_mode}'")
                    elif mode == 'bicubic':
                        if padding_mode == 'zeros':
                            if align_corners:
                                groundtruth = torch.tensor(
                                    [[-0.10424726, 7.1400003, 5.0000, 5.7842274, 9.0000],
                                     [2.4492188, 7.4814040, 5.0000, 6.0277520, 0.0000]]).view(1, 1, 2, 5)
                            else:
                                groundtruth = torch.tensor(
                                    [[0.00000, 7.6287503, 1.0625, 5.5977230, 5.3270264],
                                     [0.40625, 8.0288770, 1.0625, 5.9375067, -0.3515625]]).view(1, 1, 2, 5)
                        elif padding_mode == 'border':
                            if align_corners:
                                groundtruth = torch.tensor(
                                    [[1.1520010, 6.0599990, 5.0000, 4.870930, 9.0000000],
                                     [2.1328125, 6.4258375, 5.0000, 5.076003, 8.8671875]]).view(1, 1, 2, 5)
                            else:
                                groundtruth = torch.tensor(
                                    [[0.894531, 6.6050020, 4.625, 4.7138715, 9.800781],
                                     [0.906250, 7.2822485, 4.625, 5.0000052, 10.00000]]).view(1, 1, 2, 5)
                        elif padding_mode == 'reflection':
                            if align_corners:
                                groundtruth = torch.tensor(
                                    [[3.1822524, 6.239998, 5.0000, 4.8709273, 9.00000],
                                     [1.7812500, 6.703594, 5.0000, 5.0760007, 8.21875]]).view(1, 1, 2, 5)
                            else:
                                groundtruth = torch.tensor(
                                    [[2.7993753, 6.6050020, 4.25, 4.7138715, 10.269531],
                                     [0.8125000, 7.2822485, 4.25, 5.0000052, 9.332031]]).view(1, 1, 2, 5)
                        else:
                            raise AssertionError(f"missing groundtruth test for padding mode '{padding_mode}'")

                    else:
                        raise AssertionError(f"missing groundtruth test for interpolation mode '{mode}'")
                    output = F.grid_sample(input, grid, mode=mode, padding_mode=padding_mode,
                                           align_corners=align_corners)
                    self.assertEqual(output, groundtruth, atol=1e-5, rtol=0,
                                     msg=f"groundtruth comparison failed for mode={mode}, "
                                     f"padding_mode={padding_mode}")

                    # See NOTE [ grid_sample CPU fallback ]
                    output = torch._grid_sampler_2d_cpu_fallback(
                        input.float(), grid.float(),
                        F.GRID_SAMPLE_INTERPOLATION_MODES[mode],
                        F.GRID_SAMPLE_PADDING_MODES[padding_mode],
                        align_corners)
                    self.assertEqual(output, groundtruth.float(), atol=1e-5, rtol=0)

                    # explicit check for gradient edge cases
                    input = torch.arange(0., 5).expand((1, 1, 5, 5))
                    grid = torch.tensor(
                        [[[1.0, 1.0], [1.0, -1.0], [0.8, 0.8], [0.8, -0.8]],
                         [[-1.0, -1.0], [-1.0, 1.0], [-0.8, -0.8], [-0.8, 0.8]]]).view(1, 2, 4, 2).requires_grad_()
                    if mode == 'bilinear':
                        if padding_mode == 'zeros':
                            if align_corners:
                                groundtruth = torch.tensor(
                                    [[[[-8., -8.], [-8., 0.], [2., 0.], [2., 0.]],
                                      [[2., 0.], [2., 0.], [2., 0.], [2., 0.]]]]).view(1, 2, 4, 2)
                            else:
                                groundtruth = torch.tensor(
                                    [[[[-5., -5.], [-5., 5.], [-10., -10.], [-10., 10.]],
                                      [[0., 0.], [0., 0.], [0., 0.], [0., 0.]]]]).view(1, 2, 4, 2)
                        elif padding_mode == 'border':
                            if align_corners:
                                groundtruth = torch.tensor(
                                    [[[[-0., -0.], [-0., 0.], [2., 0.], [2., 0.]],
                                      [[0., 0.], [0., 0.], [2., 0.], [2., 0.]]]]).view(1, 2, 4, 2)
                            else:
                                groundtruth = torch.tensor(
                                    [[[[-0., -0.], [-0., 0.], [-0., -0.], [-0., 0.]],
                                      [[0., 0.], [0., 0.], [0., 0.], [0., 0.]]]]).view(1, 2, 4, 2)
                        elif padding_mode == 'reflection':
                            if align_corners:
                                groundtruth = torch.tensor(
                                    [[[[-0., -0.], [-0., 0.], [2., 0.], [2., 0.]],
                                      [[0., 0.], [0., 0.], [2., 0.], [2., 0.]]]]).view(1, 2, 4, 2)
                            else:
                                groundtruth = torch.tensor(
                                    [[[[-0., -0.], [-0., 0.], [-0., -0.], [-0., 0.]],
                                      [[0., 0.], [0., 0.], [0., 0.], [0., 0.]]]]).view(1, 2, 4, 2)
                        else:
                            raise AssertionError(f"missing gradient groundtruth test for padding mode '{padding_mode}'")
                    elif mode == 'nearest':
                        groundtruth = torch.tensor(
                            [[[[-0., -0.], [-0., 0.], [-0., -0.], [-0., 0.]],
                              [[0., 0.], [0., 0.], [0., 0.], [0., 0.]]]]).view(1, 2, 4, 2)
                    elif mode == 'bicubic':
                        if padding_mode == 'zeros':
                            if align_corners:
                                groundtruth = torch.tensor(
                                    [[[[-4.5, -6.], [-4.5, 6.], [2.725679, 0.740878], [2.725679, -0.740878]],
                                      [[1.5, 0.], [1.5, 0.], [1.927921, -0.05688], [1.927921, 0.05688]]]]).view(1, 2, 4, 2)
                            else:
                                groundtruth = torch.tensor(
                                    [[[[-5.859375, -5.888672], [-5.859375, 5.888672], [-5.6250, -7.5000], [-5.6250, 7.5000]],
                                      [[-0.234375, -0.263672], [-0.234375, 0.263672], [1.8750, 0.], [1.8750, 0.]]]]
                                ).view(1, 2, 4, 2)
                        elif padding_mode == 'border':
                            if align_corners:
                                groundtruth = torch.tensor(
                                    [[[[1.5, 0.], [1.5, 0.], [1.74, 0.], [1.74, 0.]],
                                      [[1.5, 0.], [1.5, 0.], [1.74, 0.], [1.74, 0.]]]]).view(1, 2, 4, 2)
                            else:
                                groundtruth = torch.tensor(
                                    [[[[-0.46875, 0.], [-0.46875, 0.], [1.8750, 0.], [1.8750, 0.]],
                                      [[-0.46875, 0.], [-0.46875, 0.], [1.8750, 0.], [1.8750, 0.]]]]).view(1, 2, 4, 2)
                        elif padding_mode == 'reflection':
                            if align_corners:
                                groundtruth = torch.tensor(
                                    [[[[0., 0.], [0., 0.], [1.92, 0.], [1.92, 0.]],
                                      [[0., 0.], [0., 0.], [1.92, 0.], [1.92, 0.]]]]).view(1, 2, 4, 2)
                            else:
                                groundtruth = torch.tensor(
                                    [[[[0., 0.], [0., 0.], [1.875, 0.], [1.875, 0.]],
                                      [[0., 0.], [0., 0.], [1.875, 0.], [1.875, 0.]]]]).view(1, 2, 4, 2)
                        else:
                            raise AssertionError(f"missing gradient groundtruth test for padding mode '{padding_mode}'")
                    else:
                        raise AssertionError(f"missing gradient groundtruth test for interpolation mode '{mode}'")
                    for input_requires_grad in [False, True]:
                        input = input.requires_grad_(input_requires_grad)
                        F.grid_sample(input, grid, mode=mode, padding_mode=padding_mode,
                                      align_corners=align_corners).sum().backward()
                        self.assertEqual(grid.grad, groundtruth, atol=1e-5, rtol=0,
                                         msg=f"gradient groundtruth comparison failed for mode={mode}, "
                                         f"padding_mode={padding_mode}, input_requires_grad={input_requires_grad}")
                        grid.grad.zero_()

                    # See NOTE [ grid_sample CPU fallback ]
                    torch._grid_sampler_2d_cpu_fallback(
                        input.float(), grid.float(),
                        F.GRID_SAMPLE_INTERPOLATION_MODES[mode],
                        F.GRID_SAMPLE_PADDING_MODES[padding_mode],
                        align_corners).sum().backward()
                    self.assertEqual(grid.grad, groundtruth, atol=1e-5, rtol=0)

                    # do gradcheck
                    N = random.randint(2, 8)
                    C = random.randint(2, 6)
                    H = random.randint(2, 8)
                    W = random.randint(2, 8)
                    input = torch.randn(N, C, H, W, requires_grad=True)
                    grid = torch.randn(N, H, W, 2, requires_grad=True)

                    for input_requires_grad in [False, True]:
                        input.requires_grad_(input_requires_grad)
                        self.assertTrue(gradcheck(
                            lambda inp, grd: F.grid_sample(inp, grd, mode=mode, padding_mode=padding_mode,
                                                           align_corners=align_corners),
                            (input, grid)))
                        test(N, C, H, W, mode, padding_mode, align_corners, input_requires_grad)
                        if TEST_CUDNN:
                            with cudnn.flags(enabled=False):
                                test(N, C, H, W, mode, padding_mode, align_corners, input_requires_grad)
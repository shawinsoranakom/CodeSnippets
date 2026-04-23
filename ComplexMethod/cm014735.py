def test_interpolate_buffer_overflow(self):
        # Test buffer overflow issue due to inaccurate floating point
        # representation for integer values. See issue below for details.
        # https://github.com/pytorch/pytorch/issues/88939

        def helper(size, dtype, mode, device, is_channels_last):
            input = torch.ones(size, dtype=dtype, device=device)
            if is_channels_last:
                if len(size) == 3:
                    input = input.transpose(1, 2).contiguous().transpose(1, 2)
                elif len(size) == 4:
                    input = input.to(memory_format=torch.channels_last)
                else:
                    input = input.to(memory_format=torch.channels_last_3d)
            output1 = F.interpolate(input, 2, mode=mode, align_corners=True)
            # reset the corner value and expect the output is changed as well
            # the output won't be changed on buffer overflow
            input[(-1,) * len(size)] = 0.5
            output2 = F.interpolate(input, 2, mode=mode, align_corners=True)
            self.assertNotEqual(output1, output2)

        size_dtype_list = []
        # We set the size larger than the floating point exactly representable range
        # float: exact representable range (-2**24,2**24)
        size_dtype_list.append(([1, 10, 2**24 + 4], torch.float))
        size_dtype_list.append(([1, 10, 2, 2**24 + 4], torch.float))
        size_dtype_list.append(([1, 10, 2, 2, 2**24 + 4], torch.float))
        # bfloat16: exact representable range (-2**8, 2**8)
        size_dtype_list.append(([1, 10, 2**8 + 4], torch.bfloat16))
        size_dtype_list.append(([1, 10, 2, 2**8 + 4], torch.bfloat16))
        size_dtype_list.append(([1, 10, 2, 2, 2**8 + 4], torch.bfloat16))
        # half: exact representable range (-2**11, 2**11)
        size_dtype_list.append(([1, 10, 2**11 + 4], torch.half))
        size_dtype_list.append(([1, 10, 2, 2**11 + 4], torch.half))
        size_dtype_list.append(([1, 10, 2, 2, 2**11 + 4], torch.half))

        # TODO: turn on cuda test after buffer overflow issue is fixed in cuda kernel
        # devices = ['cpu'] + (['cuda'] if torch.cuda.is_available() else [])
        devices = ['cpu']

        for mode in ('linear', 'bilinear', 'bicubic', 'trilinear'):
            for size_dtype in size_dtype_list:
                size, dtype = size_dtype
                if (
                    mode == 'linear' and len(size) != 3
                    or (mode == 'bilinear' and len(size) != 4)
                    or (mode == 'bicubic' and len(size) != 4)
                    or (mode == 'trilinear' and len(size) != 5)
                ):
                    continue
                for device in devices:
                    if (
                        device == 'cpu' and dtype == torch.half
                        or (device == 'cuda' and dtype == torch.bfloat16)
                    ):
                        # no half precision support on cpu or bfloat16 on cuda yet
                        continue
                    for is_channels_last in (True, False):
                        helper(size, dtype, mode, device, is_channels_last)
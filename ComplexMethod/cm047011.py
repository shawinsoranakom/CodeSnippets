def fast_dequantize(W, quant_state = None, out = None, use_global_buffer = False):
        if isinstance(W, Float8Tensor):
            return W.dequantize()
        if quant_state is None:
            return W
        if W.dtype == torch.float8_e4m3fn:
            return weight_dequant(W, quant_state)
        if type(quant_state) is not list:
            # New quant_state as a class
            # https://github.com/TimDettmers/bitsandbytes/pull/763/files
            absmax = quant_state.absmax
            shape = quant_state.shape
            dtype = quant_state.dtype
            blocksize = quant_state.blocksize
            offset = quant_state.offset
            state2 = quant_state.state2
            absmax2 = state2.absmax
            code2 = state2.code
            blocksize2 = state2.blocksize
        else:
            # Old quant_state as a list of lists
            absmax, shape, dtype, blocksize, compressed_stats, _, _ = quant_state
            offset, state2 = compressed_stats
            absmax2, code2, blocksize2, _, _, _, _ = state2
        pass

        n_elements_absmax = absmax.numel()
        device = W.device

        # Create weight matrix
        if out is None:
            out = torch_empty(shape, dtype = dtype, device = device, requires_grad = False)
        else:
            assert out.shape == shape
            assert out.dtype == dtype
        out_absmax = torch_empty(
            n_elements_absmax, dtype = torch_float32, device = device, requires_grad = False
        )

        # Do dequantization
        ptr_out_absmax = get_ptr(out_absmax)
        cdequantize_blockwise_fp32(
            get_ptr(code2),
            get_ptr(absmax),
            get_ptr(absmax2),
            ptr_out_absmax,
            ctypes_c_int(blocksize2),
            ctypes_c_int(n_elements_absmax),
        )
        out_absmax += offset

        fx = (
            cdequantize_blockwise_fp16_nf4
            if dtype == torch_float16
            else cdequantize_blockwise_bf16_nf4
        )
        fx(
            get_ptr(None),
            get_ptr(W),
            ptr_out_absmax,
            get_ptr(out),
            ctypes_c_int(blocksize),
            ctypes_c_int(out.numel()),
        )

        # Careful returning transposed data
        is_transposed = True if W.shape[0] == 1 else False
        return out.t() if is_transposed else out
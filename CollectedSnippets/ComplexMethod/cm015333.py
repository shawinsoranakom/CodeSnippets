def _group_quantize_tensor(self, w, n_bit=4, q_group_size=16):
        # w [k, n] = [32, 48]
        if w.dim() != 2:
            raise AssertionError(f"Expected w.dim() == 2, got {w.dim()}")
        # w [n, k] = [48, 32]
        w = w.transpose(0, 1).contiguous()
        if q_group_size <= 1:
            raise AssertionError(f"Expected q_group_size > 1, got {q_group_size}")
        if w.shape[-1] % q_group_size != 0:
            raise AssertionError(
                f"Expected w.shape[-1] % q_group_size == 0, "
                f"got {w.shape[-1]} % {q_group_size} = {w.shape[-1] % q_group_size}"
            )

        # to_quant: [n * k / group_size, group_size]
        to_quant = w.reshape(-1, q_group_size)
        nan_count = torch.isnan(to_quant).sum()
        if nan_count != 0:
            raise AssertionError(f"Expected no NaNs in to_quant, got {nan_count}")

        max_val = to_quant.amax(dim=1, keepdim=True)
        min_val = to_quant.amin(dim=1, keepdim=True)
        max_int = 2**n_bit - 1
        min_int = 0
        scales = (max_val - min_val).clamp(min=1e-6) / max_int
        nan_count = torch.isnan(scales).sum()
        if nan_count != 0:
            raise AssertionError(f"Expected no NaNs in scales, got {nan_count}")

        zeros = min_int - min_val.div(scales).round()
        zeros = torch.clamp(zeros, min_int, max_int)
        zeros = zeros.to(torch.int8)
        nan_count = torch.isnan(zeros).sum()
        if nan_count != 0:
            raise AssertionError(f"Expected no NaNs in zeros, got {nan_count}")

        out = to_quant.div(scales).add(zeros).round().clamp_(min_int, max_int)
        nan_count = torch.isnan(out).sum()
        if nan_count != 0:
            raise AssertionError(f"Expected no NaNs in out, got {nan_count}")

        # [n, k]
        out = out.to(dtype=torch.int32).reshape(w.shape)
        if out.device != torch.device("cpu"):
            out = (out[::, 1::2] << 4 | out[::, 0::2]).to(torch.uint8)

        # Scales and zeros for the same q-group should be contiguous, so we can
        # load as a 32-bit word
        scales = scales.view(w.shape[0], -1).transpose(0, 1).contiguous()
        zeros = zeros.view(w.shape[0], -1).transpose(0, 1).contiguous()

        return out, scales, zeros
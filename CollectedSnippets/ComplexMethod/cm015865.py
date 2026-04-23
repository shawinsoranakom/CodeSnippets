def _group_quantize_tensor_xpu(w, n_bit=4, q_group_size=16):
            # w [k, n] = [32, 48]
            if w.dim() != 2:
                raise AssertionError(f"Expected 2D tensor, got {w.dim()}D")
            # w [n, k] = [48, 32]
            w = w.transpose(0, 1).contiguous()
            if q_group_size <= 1:
                raise AssertionError(f"Expected q_group_size > 1, got {q_group_size}")
            if w.shape[-1] % q_group_size != 0:
                raise AssertionError(
                    f"w.shape[-1] ({w.shape[-1]}) must be divisible by q_group_size ({q_group_size})"
                )

            # to_quant: [n * k / group_size, group_size]
            to_quant = w.reshape(-1, q_group_size)
            if torch.isnan(to_quant).sum() != 0:
                raise AssertionError("to_quant contains NaN values")

            max_val = to_quant.amax(dim=1, keepdim=True)
            min_val = to_quant.amin(dim=1, keepdim=True)
            max_int = 2**n_bit - 1
            min_int = 0
            scales = (max_val - min_val).clamp(min=1e-6) / max_int
            if torch.isnan(scales).sum() != 0:
                raise AssertionError("scales contains NaN values")

            zeros = min_int - min_val.div(scales).round()
            zeros = torch.clamp(zeros, min_int, max_int)
            zeros = zeros.to(torch.int8)
            if torch.isnan(zeros).sum() != 0:
                raise AssertionError("zeros contains NaN values")

            out = to_quant.div(scales).add(zeros).round().clamp_(min_int, max_int)
            if torch.isnan(out).sum() != 0:
                raise AssertionError("out contains NaN values")

            # [n, k]
            out = out.to(dtype=torch.int32).reshape(w.shape)
            if out.device != torch.device("cpu"):
                out = (out[::, 1::2] << 4 | out[::, 0::2]).to(torch.uint8)

            # Scales and zeros for the same q-group should be contiguous, so we can
            # load as a 32-bit word
            scales = scales.view(w.shape[0], -1).transpose(0, 1).contiguous()
            zeros = zeros.view(w.shape[0], -1).transpose(0, 1).contiguous()

            return out, scales, zeros
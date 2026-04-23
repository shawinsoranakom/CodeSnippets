def _get_ref_params(reduce_range, qscheme, dtype, input_scale, min_val, max_val):
            if dtype not in _INT_DTYPES:
                raise AssertionError(f"Not supported dtype: {dtype}, supported dtypes are {_INT_DTYPES}")
            eps = torch.tensor([tolerance])
            if dtype in [torch.qint8, torch.int8]:
                if reduce_range:
                    quant_min, quant_max = -64, 63
                else:
                    quant_min, quant_max = -128, 127
            elif dtype in [torch.quint8, torch.uint8]:
                if reduce_range:
                    quant_min, quant_max = 0, 127
                else:
                    quant_min, quant_max = 0, 255
            elif dtype == torch.int16:
                quant_min, quant_max = -1 * (2 ** 15), (2 ** 15) - 1
            elif dtype == torch.uint16:
                quant_min, quant_max = 0, (2 ** 16) - 1
            elif dtype in [torch.qint32, torch.int32]:
                quant_min, quant_max = -1 * (2 ** 31), (2 ** 31) - 1

            min_val_neg = torch.tensor([0.])
            max_val_pos = torch.tensor([input_scale * max_val]) if qdtype is torch.qint32 else torch.tensor([max_val])

            scale, zero_point = 1.0, 0
            if qscheme == torch.per_tensor_symmetric or qscheme == torch.per_channel_symmetric:
                scale = torch.max(-min_val_neg, max_val_pos) / (float(quant_max - quant_min) / 2)
                scale = torch.max(scale, eps)
                if dtype in [torch.quint8, torch.uint8]:
                    zero_point = 128
                if dtype == torch.uint16:
                    zero_point = 2 ** 15
            else:
                scale = torch.max((max_val_pos - min_val_neg) / float(quant_max - quant_min), eps)
                zero_point = quant_min - torch.round(min_val_neg / scale).to(torch.int)
                zero_point = torch.clamp(zero_point, quant_min, quant_max)

            return scale, zero_point
def _clean_attr(mod: torch.nn.Module):
        for submod in mod.modules():
            attr_names_to_clean = set()
            for k, v in submod.__dict__.items():
                if isinstance(v, torch.ScriptObject):
                    attr_names_to_clean.add(k)
                if k == "_buffers":
                    buffer_name_to_clean = set()

                    for b_name, b_value in v.items():
                        if isinstance(b_value, torch.Tensor) and b_value.dtype in [
                            torch.qint8,
                            torch.quint8,
                        ]:
                            buffer_name_to_clean.add(b_name)
                    for b_name in buffer_name_to_clean:
                        v.pop(b_name, None)
            for attr_name in attr_names_to_clean:
                delattr(submod, attr_name)
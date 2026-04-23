def _apply(self, fn, recurse=True):  # This is to get torch.compile + moving weights to another device working
                if recurse:
                    for module in self.children():
                        module._apply(fn)

                for key, param in self._parameters.items():
                    if param is None:
                        continue
                    p = fn(param)
                    if (not torch.is_inference_mode_enabled()) and p.is_inference():
                        p = p.clone()
                    self.register_parameter(key, torch.nn.Parameter(p, requires_grad=False))
                for key, buf in self._buffers.items():
                    if buf is not None:
                        self._buffers[key] = fn(buf)
                return self
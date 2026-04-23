def _save_to_state_dict(self: _LazyProtocol, destination, prefix, keep_vars):
        # This should be ideally implemented as a hook,
        # but we should override `detach` in the UninitializedParameter to return itself
        # which is not clean
        for name, param in self._parameters.items():
            if param is not None:
                if not (is_lazy(param) or keep_vars):
                    param = param.detach()
                destination[prefix + name] = param
        for name, buf in self._buffers.items():
            if buf is not None and name not in self._non_persistent_buffers_set:
                if not (is_lazy(buf) or keep_vars):
                    buf = buf.detach()
                destination[prefix + name] = buf
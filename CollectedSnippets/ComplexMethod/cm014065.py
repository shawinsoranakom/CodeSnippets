def to_proxy(self, t: Any) -> Any:
        if t is None:
            return None
        if isinstance(t, list):
            return [self.to_proxy(x) for x in t]
        if isinstance(t, tuple):
            return tuple(self.to_proxy(x) for x in t)
        if isinstance(t, (torch.SymInt, torch.SymFloat)):
            return self.symnode_proxy_lookup[t.node]
        if not isinstance(t, torch.Tensor):
            # constant types like device, dtype, str
            return t
        proxy_tensor = fetch_object_proxy(self.fx_tracer, t)
        assert isinstance(proxy_tensor, torch.fx.experimental.proxy_tensor._ProxyTensor)
        return proxy_tensor.proxy
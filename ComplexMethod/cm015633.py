def test_einops_method(self, method):
        flag = einops.__version__ >= "0.8.2"
        if not hasattr(einops, method):
            self.skipTest(f"Needs einops.{method}")

        if method == "reduce":
            einops_method = f"einops_einops_{method}"
            snippet = "y = einops.reduce(x, 'a b c -> a b', 'min')"
        elif method == "repeat":
            einops_method = f"einops_einops_{method}"
            snippet = "y = einops.repeat(x, 'a b c -> a b c d', d=2)"
        elif method == "rearrange":
            einops_method = f"einops_einops_{method}"
            snippet = "y = einops.rearrange(x, 'a b c -> a c b')"
        elif method == "einsum":
            einops_method = f"einops_einops_{method}"
            snippet = "y = einops.einsum(x, 'a b c -> a c b')"
        elif method == "pack":
            einops_method = f"einops_packing_{method}"
            snippet = "y, meta = einops.pack([x], '* b')"
        elif method == "unpack":
            einops_method = f"einops_packing_{method}"
            snippet = "x_packed, meta = einops.pack([x], '* b'); y = einops.unpack(x_packed, meta, '* b')[0]"
        else:
            self.fail(method)
        self._run_in_subprocess(flag, method, einops_method, snippet)
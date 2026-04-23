def test_fused_sdp_choice(self, device, type: str):
        batch_size, seq_len, num_heads, head_dim = 2, 128, 8, 64
        shape = SdpaShape(batch_size, num_heads, seq_len, head_dim)
        make_tensor = partial(rand_sdpa_tensor, device=device, dtype=torch.float16, packed=True, requires_grad=True)

        qkv = make_tensor(shape, type=type)
        query, key, value = qkv.chunk(3, dim=-1)

        query = query.view(batch_size, -1, num_heads, head_dim).transpose(1, 2)
        value = value.view(batch_size, -1, num_heads, head_dim).transpose(1, 2)
        key = key.view(batch_size, -1, num_heads, head_dim).transpose(1, 2)

        device_capability = None
        if "cuda" in str(device):
            device_capability = torch.cuda.get_device_capability()
        prefer_cudnn = "TORCH_CUDNN_SDPA_PREFERRED" not in os.environ or bool(os.environ["TORCH_CUDNN_SDPA_PREFERRED"])
        # cuDNN prioritization requires cuDNN > 9.15.0 (91500) per sdp_utils.cpp:83
        cudnn_version = torch.backends.cudnn.version() if torch.backends.cudnn.is_available() else 0
        is_hopper_or_newer = device_capability and (device_capability[0] == 9 or device_capability[0] == 10)
        prefer_cudnn = prefer_cudnn and is_hopper_or_newer and cudnn_version > 91500

        # cuDNN is enabled by default on SM 9.0/10.0 with cuDNN > 9.15.0 (per #169849)
        # For older cuDNN versions or other architectures, Flash Attention is preferred
        if type != "nested" and PLATFORM_SUPPORTS_CUDNN_ATTENTION and prefer_cudnn:
            self.assertEqual(torch._fused_sdp_choice(query, key, value), SDPBackend.CUDNN_ATTENTION.value)
        elif PLATFORM_SUPPORTS_FLASH_ATTENTION:
            self.assertEqual(torch._fused_sdp_choice(query, key, value), SDPBackend.FLASH_ATTENTION.value)
        elif type != "nested" and PLATFORM_SUPPORTS_CUDNN_ATTENTION and not prefer_cudnn:  # e.g., we're on Windows
            self.assertEqual(torch._fused_sdp_choice(query, key, value), SDPBackend.EFFICIENT_ATTENTION.value)
            with sdpa_kernel(backends=[SDPBackend.CUDNN_ATTENTION]):
                self.assertEqual(torch._fused_sdp_choice(query, key, value), SDPBackend.CUDNN_ATTENTION.value)
        else:
            self.assertEqual(torch._fused_sdp_choice(query, key, value), SDPBackend.EFFICIENT_ATTENTION.value)

        # Change dtype to float32 so that efficient attention should get chosen
        make_tensor = partial(rand_sdpa_tensor, device=device, dtype=torch.float32, packed=True)

        qkv = make_tensor(shape, type=type)
        query, key, value = qkv.chunk(3, dim=-1)

        query = query.view(batch_size, -1, num_heads, head_dim).transpose(1, 2)
        value = value.view(batch_size, -1, num_heads, head_dim).transpose(1, 2)
        key = key.view(batch_size, -1, num_heads, head_dim).transpose(1, 2)

        if torch._fused_sdp_choice(query, key, value) != SDPBackend.EFFICIENT_ATTENTION.value:
            raise AssertionError("expected EFFICIENT_ATTENTION backend")
def test_nan_assert(self, type):
        # Expecting a device-side error when NaN is detected
        os.environ["TORCH_NCCL_NAN_CHECK"] = "1"
        store = c10d.FileStore(self.file_name, self.world_size)
        pg = self._create_process_group_nccl(store, self.opts())
        backend = pg._get_backend(torch.device("cuda"))

        device = self.rank_to_GPU[self.rank][0]
        # Cover different buffer sizes
        if type == torch.float64:
            size = (1024,)  # 1K elements
        elif type == torch.float32:
            size = (1024, 1024)  # 1M elements
        elif type == torch.float16:
            size = (1024, 1024, 1024)  # 1G elements
        else:
            size = (1,)  # 1 element

        # Note: currently we cannot fill values into a FP8 tensor, thus we
        # create the NaN tensor in float32 type and cast it to FP8
        if type == torch.float8_e4m3fn or type == torch.float8_e5m2:
            init_type = torch.float32
        else:
            init_type = type

        nan_tensor = torch.zeros(*size, dtype=init_type, device=device)
        # randomly pick an nan element
        index = tuple([random.randrange(size[i]) for i in range(len(size))])
        nan_tensor[index] = float("nan")
        if init_type != type:
            # Now cast to the targeted dtype
            nan_tensor = nan_tensor.to(type)

        output = torch.empty(self.world_size, *size, dtype=type, device=device)

        # confirm enable/disable flag works
        backend._set_enable_nan_check(False)
        # Note: using all-gather here bc some NCCL/SM version does not support
        # FP8 reduction
        # temporarily skip due to https://github.com/pytorch/pytorch/issues/153479
        # pg._allgather_base(output, nan_tensor)

        backend._set_enable_nan_check(True)
        try:
            pg._allgather_base(output, nan_tensor)
        except Exception:
            sys.exit(signal.SIGABRT)

        dist.destroy_process_group()

        # reset env
        os.environ["TORCH_NCCL_NAN_CHECK"] = "0"
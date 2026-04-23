def compare_with_numpy(self, torch_fn, np_fn, tensor_like,
                           device=None, dtype=None, **kwargs):
        if not TEST_NUMPY:
            raise AssertionError("TEST_NUMPY must be True to use compare_with_numpy")

        if isinstance(tensor_like, torch.Tensor):
            if device is not None:
                raise AssertionError("device must be None when tensor_like is a Tensor")
            if dtype is not None:
                raise AssertionError("dtype must be None when tensor_like is a Tensor")
            t_cpu = tensor_like.detach().cpu()
            if t_cpu.dtype is torch.bfloat16:
                t_cpu = t_cpu.float()
            a = t_cpu.numpy()
            t = tensor_like
        else:
            d = copy.copy(torch_to_numpy_dtype_dict)
            d[torch.bfloat16] = np.float32
            a = np.array(tensor_like, dtype=d[dtype])
            t = torch.tensor(tensor_like, device=device, dtype=dtype)

        np_result = np_fn(a)
        torch_result = torch_fn(t).cpu()

        # Converts arrays to tensors
        if isinstance(np_result, np.ndarray):
            try:
                np_result = torch.from_numpy(np_result)
            except Exception:
                # NOTE: copying an array before conversion is necessary when,
                #   for example, the array has negative strides.
                np_result = torch.from_numpy(np_result.copy())
            if t.dtype is torch.bfloat16 and torch_result.dtype is torch.bfloat16 and np_result.dtype is torch.float:
                torch_result = torch_result.to(torch.float)

        self.assertEqual(np_result, torch_result, **kwargs)
def extract_fbank(
        self, data, data_len=None, data_type: str = "sound", frontend=None, **kwargs
    ):
        if isinstance(data, np.ndarray):
            data = torch.from_numpy(data)
            if len(data.shape) < 2:
                data = data[None, :]  # data: [batch, N]
            data_len = [data.shape[1]] if data_len is None else data_len
        elif isinstance(data, torch.Tensor):
            if len(data.shape) < 2:
                data = data[None, :]  # data: [batch, N]
            data_len = [data.shape[1]] if data_len is None else data_len
        elif isinstance(data, (list, tuple)):
            data_list, data_len = [], []
            for data_i in data:
                if isinstance(data_i, np.ndarray):
                    data_i = torch.from_numpy(data_i)
                data_list.append(data_i)
                data_len.append(data_i.shape[0])
            data = pad_sequence(data_list, batch_first=True)

        data, data_len = frontend(data, data_len, **kwargs)

        if isinstance(data_len, (list, tuple)):
            data_len = torch.tensor([data_len])
        return data.to(torch.float32), data_len.to(torch.int32)
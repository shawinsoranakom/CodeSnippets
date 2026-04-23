def __call__(self, features, return_tensors=None, separator_id=None):
        if return_tensors is None:
            return_tensors = self.return_tensors
        if separator_id is None:
            separator_id = self.separator_id
        is_labels_provided = "labels" in features[0]
        batch = {"input_ids": [], "labels": []}
        if self.return_position_ids:
            batch.update({"position_ids": []})
        if self.return_seq_idx:
            batch.update({"seq_idx": []})
        if self.return_flash_attn_kwargs:
            cu_seq_lens = [0]
            max_length = 0
        for seq_idx, sample in enumerate(features):
            input_ids = sample["input_ids"]
            # Convert to list if tensor
            if hasattr(input_ids, "tolist"):
                input_ids = input_ids.tolist()
            batch["input_ids"] += input_ids

            if is_labels_provided:
                labels = sample["labels"]
                # Convert to list if tensor
                if hasattr(labels, "tolist"):
                    labels = labels.tolist()
                batch["labels"] += [separator_id] + labels[1:]
            else:
                batch["labels"] += [separator_id] + input_ids[1:]
            if self.return_position_ids:
                batch["position_ids"] += list(range(len(input_ids)))
            if self.return_seq_idx:
                batch["seq_idx"] += [seq_idx for _ in range(len(input_ids))]
            if self.return_flash_attn_kwargs:
                cu_seq_lens.append(cu_seq_lens[-1] + len(input_ids))
                max_length = max(max_length, len(input_ids))

        if self.return_flash_attn_kwargs:
            batch["cu_seq_lens_q"] = batch["cu_seq_lens_k"] = cu_seq_lens
            batch["max_length_q"] = batch["max_length_k"] = max_length

        # FlashAttentionKwargs and seq_idx are expected to be int32s.
        if return_tensors == "pt":
            import torch

            data_cls = torch.tensor
            dtype_64 = torch.int64
            dtype_32 = torch.int32
        elif return_tensors == "np":
            data_cls = np.array
            dtype_64 = np.int64
            dtype_32 = np.int32
        else:
            raise ValueError(f'return_tensors must be one of ("pt", "np"), {return_tensors=} not supported')

        for k, v in batch.items():
            if k in self._batch_dim_keys:
                v = [v]
            # Flash attention max_len_{q,k} are python ints
            if k not in self._py_int_keys:
                batch[k] = data_cls(v, dtype=dtype_64 if k in self._int_64_keys else dtype_32)

        return batch
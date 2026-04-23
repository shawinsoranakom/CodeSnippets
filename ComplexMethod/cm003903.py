def get_cached_task_embeddings(self, tasks_input_ids, tasks_attention_mask):
        not_cached_index = []
        not_cached_tasks = []
        total_task_features = []
        total_task_masks = []
        for idx, _ in enumerate(tasks_input_ids):
            cache_key = self._get_cache_key_at_index(tasks_input_ids, tasks_attention_mask, idx)
            if self.language_cache_prompt.has(cache_key):
                task_feature, task_mask = self.language_cache_prompt.get(cache_key)
                total_task_features.append(task_feature)
                total_task_masks.append(task_mask)
            else:
                total_task_features.append(None)
                total_task_masks.append(None)
                not_cached_index.append(idx)
                not_cached_tasks.append(cache_key)

        if not_cached_tasks:
            not_cached_index_ids = torch.stack([tasks_input_ids[idx] for idx in not_cached_index])
            not_cached_mask = torch.stack([tasks_attention_mask[idx] for idx in not_cached_index])
            embeddings, masks = self.language_backbone(not_cached_index_ids, mask=not_cached_mask, encode_type="task")

            for idx in range(embeddings.shape[1]):
                emb = embeddings[:, [idx], :]
                idx_to_put = not_cached_index[idx]
                cur_mask = torch.unsqueeze(masks[idx], dim=0).to(self.device)
                total_task_features[idx_to_put] = emb
                total_task_masks[idx_to_put] = cur_mask
                self.language_cache_prompt.put(not_cached_tasks[idx], (emb, cur_mask))

        # pad before concat if needed
        max_len = max(task.shape[0] for task in total_task_features)
        for idx, task in enumerate(total_task_features):
            if task.shape[0] < max_len:
                pad_size = max_len - task.shape[0]
                total_task_features[idx] = F.pad(task, (0, 0, 0, 0, 0, pad_size))
                total_task_masks[idx] = F.pad(total_task_masks[idx], (0, pad_size))

        total_task_features = torch.cat(total_task_features, dim=1).to(self.device)
        total_task_masks = torch.cat(total_task_masks, dim=0).to(self.device)

        return total_task_features, total_task_masks
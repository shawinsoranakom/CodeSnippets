def iter(self):
        if self.shuffle:
            if self.seed is not None:
                random.seed(self.seed)
            else:
                random.seed(self.epoch)
            if not self.ds_width:
                random.shuffle(self.img_indices)
            random.shuffle(self.img_batch_pairs)
            indices_rank_i = self.img_indices[
                self.rank : len(self.img_indices) : self.num_replicas
            ]
        else:
            indices_rank_i = self.img_indices[
                self.rank : len(self.img_indices) : self.num_replicas
            ]

        start_index = 0
        batchs_in_one_epoch = []
        for batch_tuple in self.batch_list:
            curr_w, curr_h, curr_bsz = batch_tuple
            end_index = min(start_index + curr_bsz, self.n_samples_per_replica)
            batch_ids = indices_rank_i[start_index:end_index]
            n_batch_samples = len(batch_ids)
            if n_batch_samples != curr_bsz:
                batch_ids += indices_rank_i[: (curr_bsz - n_batch_samples)]
            start_index += curr_bsz

            if len(batch_ids) > 0:
                if self.ds_width:
                    wh_ratio_current = self.wh_ratio[self.wh_ratio_sort[batch_ids]]
                    ratio_current = wh_ratio_current.mean()
                    ratio_current = (
                        ratio_current
                        if ratio_current * curr_h < self.max_w
                        else self.max_w / curr_h
                    )
                else:
                    ratio_current = None
                batch = [(curr_w, curr_h, b_id, ratio_current) for b_id in batch_ids]
                # yield batch
                batchs_in_one_epoch.append(batch)
        return batchs_in_one_epoch
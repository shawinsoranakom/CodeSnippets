def execute(cls, latents, batch_size):
        batch_size = batch_size[0]

        output_list = []
        current_batch = (None, None, None)
        processed = 0

        for i in range(len(latents)):
            # fetch new entry of list
            #samples, masks, indices = self.get_batch(latents, i)
            next_batch = cls.get_batch(latents, i, processed)
            processed += len(next_batch[2])
            # set to current if current is None
            if current_batch[0] is None:
                current_batch = next_batch
            # add previous to list if dimensions do not match
            elif next_batch[0].shape[-1] != current_batch[0].shape[-1] or next_batch[0].shape[-2] != current_batch[0].shape[-2]:
                sliced, _ = cls.slice_batch(current_batch, 1, batch_size)
                output_list.append({'samples': sliced[0][0], 'noise_mask': sliced[1][0], 'batch_index': sliced[2][0]})
                current_batch = next_batch
            # cat if everything checks out
            else:
                current_batch = cls.cat_batch(current_batch, next_batch)

            # add to list if dimensions gone above target batch size
            if current_batch[0].shape[0] > batch_size:
                num = current_batch[0].shape[0] // batch_size
                sliced, remainder = cls.slice_batch(current_batch, num, batch_size)

                for i in range(num):
                    output_list.append({'samples': sliced[0][i], 'noise_mask': sliced[1][i], 'batch_index': sliced[2][i]})

                current_batch = remainder

        #add remainder
        if current_batch[0] is not None:
            sliced, _ = cls.slice_batch(current_batch, 1, batch_size)
            output_list.append({'samples': sliced[0][0], 'noise_mask': sliced[1][0], 'batch_index': sliced[2][0]})

        #get rid of empty masks
        for s in output_list:
            if s['noise_mask'].mean() == 1.0:
                del s['noise_mask']

        return io.NodeOutput(output_list)
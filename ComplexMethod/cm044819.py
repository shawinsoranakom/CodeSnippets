def __call__(self, batch):
        """Collate's training batch from normalized text, audio and speaker identities
        PARAMS
        ------
        batch: [text_normalized, spec_normalized, wav_normalized, sid]
        """
        # Right zero-pad all one-hot text sequences to max input length
        _, ids_sorted_decreasing = torch.sort(torch.LongTensor([x[1].size(1) for x in batch]), dim=0, descending=True)

        max_ssl_len = max([x[0].size(2) for x in batch])
        max_ssl_len = int(2 * ((max_ssl_len // 2) + 1))
        max_spec_len = max([x[1].size(1) for x in batch])
        max_spec_len = int(2 * ((max_spec_len // 2) + 1))
        max_wav_len = max([x[2].size(1) for x in batch])
        max_text_len = max([x[3].size(0) for x in batch])

        ssl_lengths = torch.LongTensor(len(batch))
        spec_lengths = torch.LongTensor(len(batch))
        wav_lengths = torch.LongTensor(len(batch))
        text_lengths = torch.LongTensor(len(batch))

        spec_padded = torch.FloatTensor(len(batch), batch[0][1].size(0), max_spec_len)
        wav_padded = torch.FloatTensor(len(batch), 1, max_wav_len)
        ssl_padded = torch.FloatTensor(len(batch), batch[0][0].size(1), max_ssl_len)
        text_padded = torch.LongTensor(len(batch), max_text_len)

        spec_padded.zero_()
        wav_padded.zero_()
        ssl_padded.zero_()
        text_padded.zero_()

        if self.is_v2Pro:
            sv_embs = torch.FloatTensor(len(batch), 20480)

        for i in range(len(ids_sorted_decreasing)):
            row = batch[ids_sorted_decreasing[i]]

            ssl = row[0]
            ssl_padded[i, :, : ssl.size(2)] = ssl[0, :, :]
            ssl_lengths[i] = ssl.size(2)

            spec = row[1]
            spec_padded[i, :, : spec.size(1)] = spec
            spec_lengths[i] = spec.size(1)

            wav = row[2]
            wav_padded[i, :, : wav.size(1)] = wav
            wav_lengths[i] = wav.size(1)

            text = row[3]
            text_padded[i, : text.size(0)] = text
            text_lengths[i] = text.size(0)

            if self.is_v2Pro:
                sv_embs[i] = row[4]
        if self.is_v2Pro:
            return (
                ssl_padded,
                ssl_lengths,
                spec_padded,
                spec_lengths,
                wav_padded,
                wav_lengths,
                text_padded,
                text_lengths,
                sv_embs,
            )
        else:
            return (
                ssl_padded,
                ssl_lengths,
                spec_padded,
                spec_lengths,
                wav_padded,
                wav_lengths,
                text_padded,
                text_lengths,
            )
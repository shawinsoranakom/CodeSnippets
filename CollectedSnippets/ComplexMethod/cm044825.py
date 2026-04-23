def forward(self, y, y_lengths, text, text_lengths, ge, speed=1, test=None, result_length:int=None, overlap_frames:torch.Tensor=None, padding_length:int=None):
        y_mask = torch.unsqueeze(commons.sequence_mask(y_lengths, y.size(2)), 1).to(y.dtype)

        y = self.ssl_proj(y * y_mask) * y_mask

        y = self.encoder_ssl(y * y_mask, y_mask)

        text_mask = torch.unsqueeze(commons.sequence_mask(text_lengths, text.size(1)), 1).to(y.dtype)
        if test == 1:
            text[:, :] = 0
        text = self.text_embedding(text).transpose(1, 2)
        text = self.encoder_text(text * text_mask, text_mask)
        y = self.mrte(y, y_mask, text, text_mask, ge)

        if padding_length is not None and padding_length!=0:
            y = y[:, :, :-padding_length]
            y_mask = y_mask[:, :, :-padding_length]


        y = self.encoder2(y * y_mask, y_mask)

        if result_length is not None:
            y = y[:, :, -result_length:]
            y_mask = y_mask[:, :, -result_length:]

        if overlap_frames is not None:
            overlap_len = overlap_frames.shape[-1]
            window = WINDOW.get(overlap_len, None)
            if window is None:
                # WINDOW[overlap_len] = torch.hann_window(overlap_len*2, device=y.device, dtype=y.dtype)
                WINDOW[overlap_len] = torch.sin(torch.arange(overlap_len*2, device=y.device) * torch.pi / (overlap_len*2))
                window = WINDOW[overlap_len]


            window = window.to(y.device)
            y[:,:,:overlap_len] = (
                window[:overlap_len].view(1, 1, -1) * y[:,:,:overlap_len]
                + window[overlap_len:].view(1, 1, -1) * overlap_frames
            )

        y_ = y
        y_mask_ = y_mask



        if speed != 1:
            y = F.interpolate(y, size=int(y.shape[-1] / speed) + 1, mode="linear")
            y_mask = F.interpolate(y_mask, size=y.shape[-1], mode="nearest")
        stats = self.proj(y) * y_mask
        m, logs = torch.split(stats, self.out_channels, dim=1)
        return y, m, logs, y_mask, y_, y_mask_
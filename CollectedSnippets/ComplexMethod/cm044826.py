def decode_streaming(self, codes, text, refer, noise_scale=0.5, speed=1, sv_emb=None, result_length:int=None, overlap_frames:torch.Tensor=None, padding_length:int=None):
        def get_ge(refer, sv_emb):
            ge = None
            if refer is not None:
                refer_lengths = torch.LongTensor([refer.size(2)]).to(refer.device)
                refer_mask = torch.unsqueeze(commons.sequence_mask(refer_lengths, refer.size(2)), 1).to(refer.dtype)
                if self.version == "v1":
                    ge = self.ref_enc(refer * refer_mask, refer_mask)
                else:
                    ge = self.ref_enc(refer[:, :704] * refer_mask, refer_mask)
                if self.is_v2pro:
                    sv_emb = self.sv_emb(sv_emb)  # B*20480->B*512
                    ge += sv_emb.unsqueeze(-1)
                    ge = self.prelu(ge)
            return ge

        if type(refer) == list:
            ges = []
            for idx, _refer in enumerate(refer):
                ge = get_ge(_refer, sv_emb[idx] if self.is_v2pro else None)
                ges.append(ge)
            ge = torch.stack(ges, 0).mean(0)
        else:
            ge = get_ge(refer, sv_emb)

        y_lengths = torch.LongTensor([codes.size(2) * 2]).to(codes.device)
        text_lengths = torch.LongTensor([text.size(-1)]).to(text.device)

        quantized = self.quantizer.decode(codes)
        if self.semantic_frame_rate == "25hz":
            quantized = F.interpolate(quantized, size=int(quantized.shape[-1] * 2), mode="nearest")
            result_length = (2*result_length) if result_length is not None else None
            padding_length = (2*padding_length) if padding_length is not None else None
        x, m_p, logs_p, y_mask, y_, y_mask_ = self.enc_p(
            quantized,
            y_lengths,
            text,
            text_lengths,
            self.ge_to512(ge.transpose(2, 1)).transpose(2, 1) if self.is_v2pro else ge,
            speed,
            result_length=result_length, 
            overlap_frames=overlap_frames, 
            padding_length=padding_length
            )
        z_p = m_p + torch.randn_like(m_p) * torch.exp(logs_p) * noise_scale

        z = self.flow(z_p, y_mask, g=ge, reverse=True)

        o = self.dec((z * y_mask)[:, :, :], g=ge)
        return o, y_, y_mask_
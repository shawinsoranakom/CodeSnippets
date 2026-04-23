def forward(
        self,
        prompts: LongTensor,
        ref_seq: LongTensor,
        text_seq: LongTensor,
        ref_bert: torch.Tensor,
        text_bert: torch.Tensor,
        top_k: LongTensor,
    ):
        bert = torch.cat([ref_bert.T, text_bert.T], 1)
        all_phoneme_ids = torch.cat([ref_seq, text_seq], 1)
        bert = bert.unsqueeze(0)

        x = self.ar_text_embedding(all_phoneme_ids)

        # avoid dtype inconsistency when exporting
        bert = bert.to(dtype=self.bert_proj.weight.dtype)

        x = x + self.bert_proj(bert.transpose(1, 2))
        x: torch.Tensor = self.ar_text_position(x)

        early_stop_num = self.early_stop_num

        # [1,N,512] [1,N]
        # y, k, v, y_emb, x_example = self.first_stage_decoder(x, prompts)
        y = prompts
        # x_example = x[:,:,0] * 0.0

        x_len = x.shape[1]
        x_attn_mask = torch.zeros((x_len, x_len), dtype=torch.bool)

        y_emb = self.ar_audio_embedding(y)
        y_len = y_emb.shape[1]
        prefix_len = y.shape[1]
        y_pos = self.ar_audio_position(y_emb)
        xy_pos = torch.concat([x, y_pos], dim=1)

        bsz = x.shape[0]
        src_len = x_len + y_len
        x_attn_mask_pad = F.pad(
            x_attn_mask,
            (0, y_len),  ###xx的纯0扩展到xx纯0+xy纯1，(x,x+y)
            value=True,
        )
        y_attn_mask = F.pad(  ###yy的右上1扩展到左边xy的0,(y,x+y)
            torch.triu(torch.ones(y_len, y_len, dtype=torch.bool), diagonal=1),
            (x_len, 0),
            value=False,
        )
        xy_attn_mask = (
            torch.concat([x_attn_mask_pad, y_attn_mask], dim=0)
            .unsqueeze(0)
            .expand(bsz * self.num_head, -1, -1)
            .view(bsz, self.num_head, src_len, src_len)
            .to(device=x.device, dtype=torch.bool)
        )

        idx = 0
        top_k = int(top_k)

        xy_dec, k_cache, v_cache = self.t2s_transformer.process_prompt(xy_pos, xy_attn_mask, None)

        logits = self.ar_predict_layer(xy_dec[:, -1])
        logits = logits[:, :-1]
        samples = sample(logits, y, top_k=top_k, top_p=1, repetition_penalty=1.35, temperature=1.0)[0]
        y = torch.concat([y, samples], dim=1)
        y_emb = self.ar_audio_embedding(y[:, -1:])
        xy_pos = y_emb * self.ar_audio_position.x_scale + self.ar_audio_position.alpha * self.ar_audio_position.pe[
            :, y_len + idx
        ].to(dtype=y_emb.dtype, device=y_emb.device)

        stop = False
        # for idx in range(1, 50):
        for idx in range(1, 1500):
            # [1, N] [N_layer, N, 1, 512] [N_layer, N, 1, 512] [1, N, 512] [1] [1, N, 512] [1, N]
            # y, k, v, y_emb, logits, samples = self.stage_decoder(y, k, v, y_emb, x_example)
            xy_dec, k_cache, v_cache = self.t2s_transformer.decode_next_token(xy_pos, k_cache, v_cache)
            logits = self.ar_predict_layer(xy_dec[:, -1])

            if idx < 11:  ###至少预测出10个token不然不给停止（0.4s）
                logits = logits[:, :-1]

            samples = sample(logits, y, top_k=top_k, top_p=1, repetition_penalty=1.35, temperature=1.0)[0]

            y = torch.concat([y, samples], dim=1)

            if early_stop_num != -1 and (y.shape[1] - prefix_len) > early_stop_num:
                stop = True
            if torch.argmax(logits, dim=-1)[0] == self.EOS or samples[0, 0] == self.EOS:
                stop = True
            if stop:
                if y.shape[1] == 0:
                    y = torch.concat([y, torch.zeros_like(samples)], dim=1)
                break

            y_emb = self.ar_audio_embedding(y[:, -1:])
            xy_pos = y_emb * self.ar_audio_position.x_scale + self.ar_audio_position.alpha * self.ar_audio_position.pe[
                :, y_len + idx
            ].to(dtype=y_emb.dtype, device=y_emb.device)

        y[0, -1] = 0

        return y[:, -idx:].unsqueeze(0)
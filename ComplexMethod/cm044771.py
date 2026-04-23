def infer(
        self,
        x,
        x_lens,
        prompts,
        bert_feature,
        top_k: int = -100,
        early_stop_num: int = -1,
        temperature: float = 1.0,
    ):
        x = self.ar_text_embedding(x)
        x = x + self.bert_proj(bert_feature.transpose(1, 2))
        x = self.ar_text_position(x)

        # AR Decoder
        y = prompts
        prefix_len = y.shape[1]
        x_len = x.shape[1]
        x_attn_mask = torch.zeros((x_len, x_len), dtype=torch.bool)
        stop = False
        for _ in tqdm(range(1500)):
            y_emb = self.ar_audio_embedding(y)
            y_pos = self.ar_audio_position(y_emb)
            # x 和逐渐增长的 y 一起输入给模型
            xy_pos = torch.concat([x, y_pos], dim=1)
            y_len = y.shape[1]
            x_attn_mask_pad = F.pad(
                x_attn_mask,
                (0, y_len),
                value=True,
            )
            y_attn_mask = F.pad(
                torch.triu(torch.ones(y_len, y_len, dtype=torch.bool), diagonal=1),
                (x_len, 0),
                value=False,
            )
            xy_attn_mask = torch.concat([x_attn_mask_pad, y_attn_mask], dim=0).to(y.device)

            xy_dec, _ = self.h(
                (xy_pos, None),
                mask=xy_attn_mask,
            )
            logits = self.ar_predict_layer(xy_dec[:, -1])
            samples = topk_sampling(logits, top_k=top_k, top_p=1.0, temperature=temperature)

            if early_stop_num != -1 and (y.shape[1] - prefix_len) > early_stop_num:
                print("use early stop num:", early_stop_num)
                stop = True

            if torch.argmax(logits, dim=-1)[0] == self.EOS or samples[0, 0] == self.EOS:
                # print(torch.argmax(logits, dim=-1)[0] == self.EOS, samples[0, 0] == self.EOS)
                stop = True
            if stop:
                if prompts.shape[1] == y.shape[1]:
                    y = torch.concat([y, torch.zeros_like(samples)], dim=1)
                    print("bad zero prediction")
                print(f"T2S Decoding EOS [{prefix_len} -> {y.shape[1]}]")
                break
            # 本次生成的 semantic_ids 和之前的 y 构成新的 y
            # print(samples.shape)#[1,1]#第一个1是bs
            # import os
            # os._exit(2333)
            y = torch.concat([y, samples], dim=1)
        return y
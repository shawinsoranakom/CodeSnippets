def infer(self, x, prompts, bert_feature):
        top_k = self.top_k
        early_stop_num = self.early_stop_num

        x = self.onnx_encoder(x, bert_feature)

        y = prompts
        prefix_len = y.shape[1]
        x_len = x.shape[1]
        x_example = x[:, :, 0] * 0.0
        x_attn_mask = torch.matmul(x_example.transpose(0, 1), x_example)
        x_attn_mask = torch.zeros_like(x_attn_mask, dtype=torch.bool)

        stop = False
        cache = {
            "all_stage": self.num_layers,
            "k": [None] * self.num_layers,
            "v": [None] * self.num_layers,
            "y_emb": None,
            "first_infer": 1,
            "stage": 0,
        }
        for idx in range(1500):
            if cache["first_infer"] == 1:
                y_emb = self.ar_audio_embedding(y)
            else:
                y_emb = torch.cat([cache["y_emb"], self.ar_audio_embedding(y[:, -1:])], 1)
            cache["y_emb"] = y_emb
            y_pos = self.ar_audio_position(y_emb)
            if cache["first_infer"] == 1:
                xy_pos = torch.concat([x, y_pos], dim=1)
            else:
                xy_pos = y_pos[:, -1:]
            y_len = y_pos.shape[1]
            if cache["first_infer"] == 1:
                x_attn_mask_pad = F.pad(x_attn_mask, (0, y_len), value=True)
                y_attn_mask = F.pad(
                    torch.triu(torch.ones(y_len, y_len, dtype=torch.bool), diagonal=1),
                    (x_len, 0),
                    value=False,
                )
                xy_attn_mask = torch.concat([x_attn_mask_pad, y_attn_mask], dim=0)
            else:
                xy_attn_mask = torch.zeros((1, x_len + y_len), dtype=torch.bool)
            xy_dec = self.h(xy_pos, mask=xy_attn_mask, cache=cache)
            logits = self.ar_predict_layer(xy_dec[:, -1])
            samples = sample(logits[0], y, top_k=top_k, top_p=1.0, repetition_penalty=1.35)[0].unsqueeze(0)
            if early_stop_num != -1 and (y.shape[1] - prefix_len) > early_stop_num:
                stop = True
            if torch.argmax(logits, dim=-1)[0] == self.EOS or samples[0, 0] == self.EOS:
                stop = True
            if stop:
                if prompts.shape[1] == y.shape[1]:
                    y = torch.concat([y, torch.zeros_like(samples)], dim=1)
                break
            y = torch.concat([y, samples], dim=1)
            cache["first_infer"] = 0
        return y, idx
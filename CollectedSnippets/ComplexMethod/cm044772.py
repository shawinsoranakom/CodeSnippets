def infer_panel_batch_infer(
        self,
        x: List[torch.LongTensor],  #####全部文本token
        x_lens: torch.LongTensor,
        prompts: torch.LongTensor,  ####参考音频token
        bert_feature: List[torch.LongTensor],
        top_k: int = -100,
        top_p: int = 100,
        early_stop_num: int = -1,
        temperature: float = 1.0,
        repetition_penalty: float = 1.35,
        **kwargs,
    ):
        if prompts is None:
            print("Warning: Prompt free is not supported batch_infer! switch to naive_infer")
            return self.infer_panel_naive_batched(
                x,
                x_lens,
                prompts,
                bert_feature,
                top_k=top_k,
                top_p=top_p,
                early_stop_num=early_stop_num,
                temperature=temperature,
                **kwargs,
            )

        max_len = kwargs.get("max_len", x_lens.max())
        x_list = []
        for x_item, bert_item in zip(x, bert_feature):
            # max_len = max(max_len, x_item.shape[0], bert_item.shape[1])
            x_item = self.ar_text_embedding(x_item.unsqueeze(0))
            x_item = x_item + self.bert_proj(bert_item.transpose(0, 1).unsqueeze(0))
            x_item = self.ar_text_position(x_item).squeeze(0)
            # x_item = F.pad(x_item,(0,0,0,max_len-x_item.shape[0]),value=0) if x_item.shape[0]<max_len else x_item  ### padding right
            x_item = (
                F.pad(x_item, (0, 0, max_len - x_item.shape[0], 0), value=0) if x_item.shape[0] < max_len else x_item
            )  ### padding left
            x_list.append(x_item)
        x: torch.Tensor = torch.stack(x_list, dim=0)

        # AR Decoder
        y = prompts

        x_len = x.shape[1]
        stop = False

        k_cache = None
        v_cache = None
        ###################  first step ##########################
        assert y is not None, "Error: Prompt free is not supported batch_infer!"
        ref_free = False

        y_emb = self.ar_audio_embedding(y)
        y_len = y_emb.shape[1]
        prefix_len = y.shape[1]
        y_lens = torch.LongTensor([y_emb.shape[1]] * y_emb.shape[0]).to(x.device)
        y_pos = self.ar_audio_position(y_emb)
        xy_pos = torch.concat([x, y_pos], dim=1)

        ##### create mask #####
        bsz = x.shape[0]
        src_len = x_len + y_len
        y_paddind_mask = make_pad_mask_left(y_lens, y_len)
        x_paddind_mask = make_pad_mask_left(x_lens, max_len)

        # (bsz, x_len + y_len)
        padding_mask = torch.concat([x_paddind_mask, y_paddind_mask], dim=1)

        x_mask = F.pad(
            torch.zeros(x_len, x_len, dtype=torch.bool, device=x.device),
            (0, y_len),
            value=True,
        )

        y_mask = F.pad(  ###yy的右上1扩展到左边xy的0,(y,x+y)
            torch.triu(torch.ones(y_len, y_len, dtype=torch.bool, device=x.device), diagonal=1),
            (x_len, 0),
            value=False,
        )

        causal_mask = torch.concat([x_mask, y_mask], dim=0).view(1, src_len, src_len).repeat(bsz, 1, 1).to(x.device)
        # padding_mask = padding_mask.unsqueeze(1) * padding_mask.unsqueeze(2) ### [b, x+y, x+y]
        ### 上面是错误的，会导致padding的token被"看见"

        # 正确的padding_mask应该是：
        # |   pad_len   |  x_len  |  y_len  |
        # [[PAD, PAD, PAD, 1, 2, 3, 4, 5, 6],
        # [PAD, PAD, PAD, 1, 2, 3, 4, 5, 6],
        # [PAD, PAD, PAD, 1, 2, 3, 4, 5, 6],  前3行按理说也应该被mask掉，但是为了防止计算attention时不出现nan，还是保留了，不影响结果
        # [PAD, PAD, PAD, 1, 2, 3, 4, 5, 6],
        # [PAD, PAD, PAD, 1, 2, 3, 4, 5, 6],
        # [PAD, PAD, PAD, 1, 2, 3, 4, 5, 6],
        # [PAD, PAD, PAD, 1, 2, 3, 4, 5, 6],
        # [PAD, PAD, PAD, 1, 2, 3, 4, 5, 6],
        # [PAD, PAD, PAD, 1, 2, 3, 4, 5, 6]]

        padding_mask = padding_mask.view(bsz, 1, src_len).repeat(1, src_len, 1)

        attn_mask: torch.Tensor = causal_mask.logical_or(padding_mask)
        attn_mask = attn_mask.unsqueeze(1).expand(-1, self.num_head, -1, -1).bool()

        # 正确的attn_mask应该是这样的：
        # |   pad_len   |  x_len  |  y_len  |
        # [[PAD, PAD, PAD, 1, 2, 3, EOS, EOS, EOS],
        # [PAD, PAD, PAD, 1, 2, 3, EOS, EOS, EOS],
        # [PAD, PAD, PAD, 1, 2, 3, EOS, EOS, EOS],  前3行按理说也应该被mask掉，但是为了防止计算attention时不出现nan，还是保留了，不影响结果
        # [PAD, PAD, PAD, 1, 2, 3, EOS, EOS, EOS],
        # [PAD, PAD, PAD, 1, 2, 3, EOS, EOS, EOS],
        # [PAD, PAD, PAD, 1, 2, 3, EOS, EOS, EOS],
        # [PAD, PAD, PAD, 1, 2, 3,   4, EOS, EOS],
        # [PAD, PAD, PAD, 1, 2, 3,   4,   5, EOS],
        # [PAD, PAD, PAD, 1, 2, 3,   4,   5,   6]]

        ###### decode #####
        y_list = [None] * y.shape[0]
        batch_idx_map = list(range(y.shape[0]))
        idx_list = [None] * y.shape[0]
        for idx in tqdm(range(1500)):
            if idx == 0:
                xy_dec, k_cache, v_cache = self.t2s_transformer.process_prompt(xy_pos, attn_mask, None)
            else:
                xy_dec, k_cache, v_cache = self.t2s_transformer.decode_next_token(xy_pos, k_cache, v_cache, attn_mask)
            logits = self.ar_predict_layer(xy_dec[:, -1])

            if idx == 0:
                attn_mask = F.pad(attn_mask[:, :, -1].unsqueeze(-2), (0, 1), value=False)
            else:
                attn_mask = F.pad(attn_mask, (0, 1), value=False)

            if idx < 11:  ###至少预测出10个token不然不给停止（0.4s）
                logits = logits[:, :-1] 

            samples = sample(
                logits, y, top_k=top_k, top_p=top_p, repetition_penalty=repetition_penalty, temperature=temperature
            )[0]

            y = torch.concat([y, samples], dim=1)

            ####### 移除batch中已经生成完毕的序列,进一步优化计算量
            tokens = torch.argmax(logits, dim=-1)
            reserved_idx_of_batch_for_y = None
            if (self.EOS in samples[:, 0]) or (self.EOS in tokens):  ###如果生成到EOS，则停止
                l1 = samples[:, 0] == self.EOS
                l2 = tokens == self.EOS
                l = l1.logical_or(l2)
                removed_idx_of_batch_for_y = torch.where(l == True)[0].tolist()
                reserved_idx_of_batch_for_y = torch.where(l == False)[0]
                # batch_indexs = torch.tensor(batch_idx_map, device=y.device)[removed_idx_of_batch_for_y]
                for i in removed_idx_of_batch_for_y:
                    batch_index = batch_idx_map[i]
                    idx_list[batch_index] = idx
                    y_list[batch_index] = y[i, :-1]

                batch_idx_map = [batch_idx_map[i] for i in reserved_idx_of_batch_for_y.tolist()]

            # 只保留batch中未生成完毕的序列
            if reserved_idx_of_batch_for_y is not None:
                # index = torch.LongTensor(batch_idx_map).to(y.device)
                y = torch.index_select(y, dim=0, index=reserved_idx_of_batch_for_y)
                attn_mask = torch.index_select(attn_mask, dim=0, index=reserved_idx_of_batch_for_y)
                if k_cache is not None:
                    for i in range(len(k_cache)):
                        k_cache[i] = torch.index_select(k_cache[i], dim=0, index=reserved_idx_of_batch_for_y)
                        v_cache[i] = torch.index_select(v_cache[i], dim=0, index=reserved_idx_of_batch_for_y)

            if (early_stop_num != -1 and (y.shape[1] - prefix_len) > early_stop_num) or idx == 1499:
                print("use early stop num:", early_stop_num)
                stop = True
                for i, batch_index in enumerate(batch_idx_map):
                    batch_index = batch_idx_map[i]
                    idx_list[batch_index] = idx
                    y_list[batch_index] = y[i, :-1]

            if None not in idx_list:
                stop = True

            if stop:
                if y.shape[1] == 0:
                    y = torch.concat([y, torch.zeros_like(samples)], dim=1)
                    print("bad zero prediction")
                print(f"T2S Decoding EOS [{prefix_len} -> {y.shape[1]}]")
                break

            ####################### update next step ###################################
            y_emb = self.ar_audio_embedding(y[:, -1:])
            xy_pos = y_emb * self.ar_audio_position.x_scale + self.ar_audio_position.alpha * self.ar_audio_position.pe[
                :, y_len + idx
            ].to(dtype=y_emb.dtype, device=y_emb.device)

        if None in idx_list:
            for i in range(x.shape[0]):
                if idx_list[i] is None:
                    idx_list[i] = 1500 - 1  ###如果没有生成到EOS，就用最大长度代替

        if ref_free:
            return y_list, [0] * x.shape[0]
        # print(idx_list)
        return y_list, idx_list
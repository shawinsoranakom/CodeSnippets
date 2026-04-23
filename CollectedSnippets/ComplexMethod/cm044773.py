def infer_panel_naive(
        self,
        x: torch.LongTensor,  #####全部文本token
        x_lens: torch.LongTensor,
        prompts: torch.LongTensor,  ####参考音频token
        bert_feature: torch.LongTensor,
        top_k: int = -100,
        top_p: int = 100,
        early_stop_num: int = -1,
        temperature: float = 1.0,
        repetition_penalty: float = 1.35,
        streaming_mode: bool = False,
        chunk_length: int = 24,
        **kwargs,
    ):
        mute_emb_sim_matrix = kwargs.get("mute_emb_sim_matrix", None)
        chunk_split_thershold = kwargs.get("chunk_split_thershold", 0.3)
        check_token_num = 2


        x = self.ar_text_embedding(x)
        x = x + self.bert_proj(bert_feature.transpose(1, 2))
        x = self.ar_text_position(x)

        # AR Decoder
        y = prompts

        x_len = x.shape[1]
        x_attn_mask = torch.zeros((x_len, x_len), dtype=torch.bool)
        stop = False
        # print(1111111,self.num_layers)

        k_cache = None
        v_cache = None
        ###################  first step ##########################
        if y is not None:
            y_emb = self.ar_audio_embedding(y)
            y_len = y_emb.shape[1]
            prefix_len = y.shape[1]
            y_pos = self.ar_audio_position(y_emb)
            xy_pos = torch.concat([x, y_pos], dim=1)
            ref_free = False
        else:
            y_emb = None
            y_len = 0
            prefix_len = 0
            y_pos = None
            xy_pos = x
            y = torch.zeros(x.shape[0], 0, dtype=torch.int, device=x.device)
            ref_free = True

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

        token_counter = 0
        curr_ptr = prefix_len
        for idx in tqdm(range(1500)):
            token_counter+=1
            if xy_attn_mask is not None:
                xy_dec, k_cache, v_cache = self.t2s_transformer.process_prompt(xy_pos, xy_attn_mask, None)
            else:
                xy_dec, k_cache, v_cache = self.t2s_transformer.decode_next_token(xy_pos, k_cache, v_cache)

            logits = self.ar_predict_layer(xy_dec[:, -1])

            if idx == 0:
                xy_attn_mask = None
            if idx < 11:  ###至少预测出10个token不然不给停止（0.4s）
                logits = logits[:, :-1]

            samples = sample(
                logits, y, top_k=top_k, top_p=top_p, repetition_penalty=repetition_penalty, temperature=temperature
            )[0]

            y = torch.concat([y, samples], dim=1)

            if early_stop_num != -1 and (y.shape[1] - prefix_len) > early_stop_num:
                print("use early stop num:", early_stop_num)
                stop = True

            if torch.argmax(logits, dim=-1)[0] == self.EOS or samples[0, 0] == self.EOS:
                stop = True
                y=y[:, :-1]
                token_counter -= 1

            if idx == 1499:
                stop = True

            if stop:
                if y.shape[1] == 0:
                    y = torch.concat([y, torch.zeros_like(samples)], dim=1)
                    print("bad zero prediction")
                # print(f"T2S Decoding EOS [{prefix_len} -> {y.shape[1]}]")
                if streaming_mode:
                    yield y[:, curr_ptr:] if curr_ptr<y.shape[1] else None, True
                break


            if streaming_mode and (mute_emb_sim_matrix is not None) and (token_counter >= chunk_length+check_token_num):
                score = mute_emb_sim_matrix[y[0, curr_ptr:]] - chunk_split_thershold
                score[score<0]=-1
                score[:-1]=score[:-1]+score[1:] ##考虑连续两个token
                argmax_idx = score.argmax()

                if score[argmax_idx]>=0 and argmax_idx+1>=chunk_length: 
                    print(f"\n\ncurr_ptr:{curr_ptr}")
                    yield y[:, curr_ptr:], False
                    token_counter -= argmax_idx+1
                    curr_ptr += argmax_idx+1


            elif streaming_mode and (mute_emb_sim_matrix is None) and (token_counter >= chunk_length):
                yield y[:, -token_counter:], False
                curr_ptr+=token_counter
                token_counter = 0



            ####################### update next step ###################################
            y_emb = self.ar_audio_embedding(y[:, -1:])
            xy_pos = y_emb * self.ar_audio_position.x_scale + self.ar_audio_position.alpha * self.ar_audio_position.pe[
                :, y_len + idx
            ].to(dtype=y_emb.dtype, device=y_emb.device)



        if not streaming_mode:
            if ref_free:
                yield y, 0
            yield y, idx
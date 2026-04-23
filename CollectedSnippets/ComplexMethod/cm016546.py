def process_tokens(self, tokens, device):
        end_token = self.special_tokens.get("end", None)
        pad_token = self.special_tokens.get("pad", -1)
        if end_token is None:
            cmp_token = pad_token
        else:
            cmp_token = end_token

        embeds_out = []
        attention_masks = []
        num_tokens = []

        for x in tokens:
            attention_mask = []
            tokens_temp = []
            other_embeds = []
            eos = False
            index = 0
            left_pad = False
            for y in x:
                if isinstance(y, numbers.Integral):
                    token = int(y)
                    if index == 0 and token == pad_token:
                        left_pad = True

                    if eos or (left_pad and token == pad_token):
                        attention_mask.append(0)
                    else:
                        attention_mask.append(1)
                        left_pad = False

                    tokens_temp += [token]
                    if not eos and token == cmp_token and not left_pad:
                        if end_token is None:
                            attention_mask[-1] = 0
                        eos = True
                else:
                    other_embeds.append((index, y))
                index += 1

            tokens_embed = torch.tensor([tokens_temp], device=device, dtype=torch.long)
            tokens_embed = self.transformer.get_input_embeddings()(tokens_embed, out_dtype=torch.float32)
            index = 0
            pad_extra = 0
            embeds_info = []
            for o in other_embeds:
                emb = o[1]
                if torch.is_tensor(emb):
                    emb = {"type": "embedding", "data": emb}

                extra = None
                emb_type = emb.get("type", None)
                if emb_type == "embedding":
                    emb = emb.get("data", None)
                else:
                    if hasattr(self.transformer, "preprocess_embed"):
                        emb, extra = self.transformer.preprocess_embed(emb, device=device)
                    else:
                        emb = None

                if emb is None:
                    index += -1
                    continue

                ind = index + o[0]
                emb = emb.view(1, -1, emb.shape[-1]).to(device=device, dtype=torch.float32)
                emb_shape = emb.shape[1]
                if emb.shape[-1] == tokens_embed.shape[-1]:
                    tokens_embed = torch.cat([tokens_embed[:, :ind], emb, tokens_embed[:, ind:]], dim=1)
                    attention_mask = attention_mask[:ind] + [1] * emb_shape + attention_mask[ind:]
                    index += emb_shape - 1
                    embeds_info.append({"type": emb_type, "index": ind, "size": emb_shape, "extra": extra})
                else:
                    index += -1
                    pad_extra += emb_shape
                    logging.warning("WARNING: shape mismatch when trying to apply embedding, embedding will be ignored {} != {}".format(emb.shape[-1], tokens_embed.shape[-1]))

            if pad_extra > 0:
                padd_embed = self.transformer.get_input_embeddings()(torch.tensor([[self.special_tokens["pad"]] * pad_extra], device=device, dtype=torch.long), out_dtype=torch.float32)
                tokens_embed = torch.cat([tokens_embed, padd_embed], dim=1)
                attention_mask = attention_mask + [0] * pad_extra

            embeds_out.append(tokens_embed)
            attention_masks.append(attention_mask)
            num_tokens.append(sum(attention_mask))

        return torch.cat(embeds_out), torch.tensor(attention_masks, device=device, dtype=torch.long), num_tokens, embeds_info
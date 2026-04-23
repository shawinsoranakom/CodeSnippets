async def _embedding(self, name, chunks):
        # Tokenization may legitimately produce zero chunks; embedding should be a no-op.
        if not chunks:
            return [], 0

        parts = sum(["full_text" in self._param.search_method, "embedding" in self._param.search_method])
        token_count = 0
        if self._canvas._kb_id:
            e, kb = KnowledgebaseService.get_by_id(self._canvas._kb_id)
            if kb.tenant_embd_id:
                embd_model_config = get_model_config_by_id(kb.tenant_embd_id)
            else:
                embd_model_config = get_model_config_by_type_and_name(self._canvas._tenant_id, LLMType.EMBEDDING, kb.embd_id)
        else:
            embd_model_config = get_tenant_default_model_by_type(self._canvas._tenant_id, LLMType.EMBEDDING)
        embedding_model = LLMBundle(self._canvas._tenant_id, embd_model_config)
        texts = []
        for c in chunks:
            txt = ""
            if isinstance(self._param.fields, str):
                self._param.fields=[self._param.fields]
            for f in self._param.fields:
                f = c.get(f)
                if isinstance(f, str):
                    txt += f
                elif isinstance(f, list):
                    txt += "\n".join(f)
            texts.append(re.sub(r"</?(table|td|caption|tr|th)( [^<>]{0,12})?>", " ", txt))
        vts, c = embedding_model.encode([name])
        token_count += c
        tts = np.concatenate([vts[0] for _ in range(len(texts))], axis=0)

        @timeout(60)
        def batch_encode(txts):
            nonlocal embedding_model
            return embedding_model.encode([truncate(c, embedding_model.max_length - 10) for c in txts])

        cnts_ = np.array([])
        for i in range(0, len(texts), settings.EMBEDDING_BATCH_SIZE):
            async with embed_limiter:
                vts, c = await thread_pool_exec(batch_encode,texts[i : i + settings.EMBEDDING_BATCH_SIZE],)
            if len(cnts_) == 0:
                cnts_ = vts
            else:
                cnts_ = np.concatenate((cnts_, vts), axis=0)
            token_count += c
            if i % 33 == 32:
                self.callback(i * 1.0 / len(texts) / parts / settings.EMBEDDING_BATCH_SIZE + 0.5 * (parts - 1))

        cnts = cnts_
        title_w = float(self._param.filename_embd_weight)
        vects = (title_w * tts + (1 - title_w) * cnts) if len(tts) == len(cnts) else cnts

        assert len(vects) == len(chunks)
        for i, ck in enumerate(chunks):
            v = vects[i].tolist()
            ck["q_%d_vec" % len(v)] = v
        return chunks, token_count
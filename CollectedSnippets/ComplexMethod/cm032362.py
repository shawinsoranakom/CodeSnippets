async def _retrieve_kb(self, query_text: str):
        kb_ids: list[str] = []
        for id in self._dataset_ids:
            if id.find("@") < 0:
                kb_ids.append(id)
                continue
            kb_nm = self._canvas.get_variable_value(id)
            # if kb_nm is a list
            kb_nm_list = kb_nm if isinstance(kb_nm, list) else [kb_nm]
            for nm_or_id in kb_nm_list:
                e, kb = KnowledgebaseService.get_by_name(nm_or_id,
                                                         self._canvas._tenant_id)
                if not e:
                    e, kb = KnowledgebaseService.get_by_id(nm_or_id)
                    if not e:
                        raise Exception(f"Dataset({nm_or_id}) does not exist.")
                kb_ids.append(kb.id)

        filtered_kb_ids: list[str] = list(set([kb_id for kb_id in kb_ids if kb_id]))

        kbs = KnowledgebaseService.get_by_ids(filtered_kb_ids)
        if not kbs:
            raise Exception("No dataset is selected.")

        embd_nms = list(set([kb.embd_id for kb in kbs]))
        assert len(embd_nms) == 1, "Knowledge bases use different embedding models."

        embd_mdl = None
        if embd_nms:
            tenant_id = self._canvas.get_tenant_id()
            embd_model_config = get_model_config_by_type_and_name(tenant_id, LLMType.EMBEDDING, embd_nms[0])
            embd_mdl = LLMBundle(tenant_id, embd_model_config)

        rerank_mdl = None
        if self._param.rerank_id:
            rerank_model_config = get_model_config_by_type_and_name(kbs[0].tenant_id, LLMType.RERANK, self._param.rerank_id)
            rerank_mdl = LLMBundle(kbs[0].tenant_id, rerank_model_config)

        vars = self.get_input_elements_from_text(query_text)
        vars = {k: o["value"] for k, o in vars.items()}
        query = self.string_format(query_text, vars)

        doc_ids = []
        if self._param.meta_data_filter != {}:
            metas = DocMetadataService.get_flatted_meta_by_kbs(kb_ids)

            def _resolve_manual_filter(flt: dict) -> dict:
                pat = re.compile(self.variable_ref_patt)
                s = flt.get("value", "")
                out_parts = []
                last = 0

                for m in pat.finditer(s):
                    out_parts.append(s[last:m.start()])
                    key = m.group(1)
                    v = self._canvas.get_variable_value(key)
                    if v is None:
                        rep = ""
                    elif isinstance(v, partial):
                        buf = []
                        for chunk in v():
                            buf.append(chunk)
                        rep = "".join(buf)
                    elif isinstance(v, str):
                        rep = v
                    else:
                        rep = json.dumps(v, ensure_ascii=False)

                    out_parts.append(rep)
                    last = m.end()

                out_parts.append(s[last:])
                flt["value"] = "".join(out_parts)
                return flt

            chat_mdl = None
            if self._param.meta_data_filter.get("method") in ["auto", "semi_auto"]:
                tenant_id = self._canvas.get_tenant_id()
                chat_model_config = get_tenant_default_model_by_type(tenant_id, LLMType.CHAT)
                chat_mdl = LLMBundle(tenant_id, chat_model_config)

            doc_ids = await apply_meta_data_filter(
                self._param.meta_data_filter,
                metas,
                query,
                chat_mdl,
                doc_ids,
                _resolve_manual_filter if self._param.meta_data_filter.get("method") == "manual" else None,
            )

        if self._param.cross_languages:
            query = await cross_languages(kbs[0].tenant_id, None, query, self._param.cross_languages)

        if kbs:
            query = re.sub(r"^user[:：\s]*", "", query, flags=re.IGNORECASE)
            kbinfos = await settings.retriever.retrieval(
                query,
                embd_mdl,
                [kb.tenant_id for kb in kbs],
                filtered_kb_ids,
                1,
                self._param.top_n,
                self._param.similarity_threshold,
                1 - self._param.keywords_similarity_weight,
                doc_ids=doc_ids,
                aggs=True,
                rerank_mdl=rerank_mdl,
                rank_feature=label_question(query, kbs),
            )
            if self.check_if_canceled("Retrieval processing"):
                return

            if self._param.toc_enhance:
                tenant_id = self._canvas._tenant_id
                chat_model_config = get_tenant_default_model_by_type(tenant_id, LLMType.CHAT)
                chat_mdl = LLMBundle(tenant_id, chat_model_config)
                cks = await settings.retriever.retrieval_by_toc(query, kbinfos["chunks"], [kb.tenant_id for kb in kbs],
                                                          chat_mdl, self._param.top_n)
                if self.check_if_canceled("Retrieval processing"):
                    return
                if cks:
                    kbinfos["chunks"] = cks
            kbinfos["chunks"] = settings.retriever.retrieval_by_children(kbinfos["chunks"],
                                                                         [kb.tenant_id for kb in kbs])
            if self._param.use_kg:
                tenant_id = self._canvas.get_tenant_id()
                chat_model_config = get_tenant_default_model_by_type(tenant_id, LLMType.CHAT)
                ck = await settings.kg_retriever.retrieval(query,
                                                     [kb.tenant_id for kb in kbs],
                                                     kb_ids,
                                                     embd_mdl,
                                                     LLMBundle(tenant_id, chat_model_config))
                if self.check_if_canceled("Retrieval processing"):
                    return
                if ck["content_with_weight"]:
                    kbinfos["chunks"].insert(0, ck)
        else:
            kbinfos = {"chunks": [], "doc_aggs": []}

        if self._param.use_kg and kbs:
            chat_model_config = get_tenant_default_model_by_type(kbs[0].tenant_id, LLMType.CHAT)
            ck = await settings.kg_retriever.retrieval(query, [kb.tenant_id for kb in kbs], filtered_kb_ids, embd_mdl,
                                                 LLMBundle(kbs[0].tenant_id, chat_model_config))
            if self.check_if_canceled("Retrieval processing"):
                return
            if ck["content_with_weight"]:
                ck["content"] = ck["content_with_weight"]
                del ck["content_with_weight"]
                kbinfos["chunks"].insert(0, ck)

        for ck in kbinfos["chunks"]:
            if "vector" in ck:
                del ck["vector"]
            if "content_ltks" in ck:
                del ck["content_ltks"]

        if not kbinfos["chunks"]:
            self.set_output("formalized_content", self._param.empty_response)
            return

        # Format the chunks for JSON output (similar to how other tools do it)
        json_output = kbinfos["chunks"].copy()

        self._canvas.add_reference(kbinfos["chunks"], kbinfos["doc_aggs"])
        form_cnt = "\n".join(kb_prompt(kbinfos, 200000, True))

        # Set both formalized content and JSON output
        self.set_output("formalized_content", form_cnt)
        self.set_output("json", json_output)

        return form_cnt
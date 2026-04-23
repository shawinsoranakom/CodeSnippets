def _set_sync():
            tenant_id = DocumentService.get_tenant_id(req["doc_id"])
            if not tenant_id:
                return get_data_error_result(message="Tenant not found!")

            e, doc = DocumentService.get_by_id(req["doc_id"])
            if not e:
                return get_data_error_result(message="Document not found!")

            tenant_embd_id = DocumentService.get_tenant_embd_id(req["doc_id"])
            if tenant_embd_id:
                embd_model_config = get_model_config_by_id(tenant_embd_id)
            else:
                embd_id = DocumentService.get_embd_id(req["doc_id"])
                if embd_id:
                    embd_model_config = get_model_config_by_type_and_name(tenant_id, LLMType.EMBEDDING, embd_id)
                else:
                    embd_model_config = get_tenant_default_model_by_type(tenant_id, LLMType.EMBEDDING)
            embd_mdl = LLMBundle(tenant_id, embd_model_config)

            _d = d
            if doc.parser_id == ParserType.QA:
                arr = [
                    t for t in re.split(
                        r"[\n\t]",
                        req["content_with_weight"]) if len(t) > 1]
                q, a = rmPrefix(arr[0]), rmPrefix("\n".join(arr[1:]))
                _d = beAdoc(d, q, a, not any(
                    [rag_tokenizer.is_chinese(t) for t in q + a]))

            v, c = embd_mdl.encode([doc.name, content_with_weight if not _d.get("question_kwd") else "\n".join(_d["question_kwd"])])
            v = 0.1 * v[0] + 0.9 * v[1] if doc.parser_id != ParserType.QA else v[1]
            _d["q_%d_vec" % len(v)] = v.tolist()
            settings.docStoreConn.update({"id": req["chunk_id"]}, _d, search.index_name(tenant_id), doc.kb_id)

            # update image
            image_base64 = req.get("image_base64", None)
            img_id = req.get("img_id", "")
            if image_base64 and img_id and "-" in img_id:
                bkt, name = img_id.split("-", 1)
                image_binary = base64.b64decode(image_base64)
                settings.STORAGE_IMPL.put(bkt, name, image_binary)
            return get_json_result(data=True)
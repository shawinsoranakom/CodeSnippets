def _create_sync():
            e, doc = DocumentService.get_by_id(req["doc_id"])
            if not e:
                resp = get_data_error_result(message="Document not found!")
                _log_response(resp, RetCode.DATA_ERROR, "Document not found!")
                return resp
            d["kb_id"] = [doc.kb_id]
            d["docnm_kwd"] = doc.name
            d["title_tks"] = rag_tokenizer.tokenize(doc.name)
            d["doc_id"] = doc.id

            tenant_id = DocumentService.get_tenant_id(req["doc_id"])
            if not tenant_id:
                resp = get_data_error_result(message="Tenant not found!")
                _log_response(resp, RetCode.DATA_ERROR, "Tenant not found!")
                return resp

            e, kb = KnowledgebaseService.get_by_id(doc.kb_id)
            if not e:
                resp = get_data_error_result(message="Knowledgebase not found!")
                _log_response(resp, RetCode.DATA_ERROR, "Knowledgebase not found!")
                return resp
            if kb.pagerank:
                d[PAGERANK_FLD] = kb.pagerank

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

            if image_base64:
                d["img_id"] = "{}-{}".format(doc.kb_id, chunck_id)
                d["doc_type_kwd"] = "image"

            v, c = embd_mdl.encode([doc.name, req["content_with_weight"] if not d["question_kwd"] else "\n".join(d["question_kwd"])])
            v = 0.1 * v[0] + 0.9 * v[1]
            d["q_%d_vec" % len(v)] = v.tolist()
            settings.docStoreConn.insert([d], search.index_name(tenant_id), doc.kb_id)

            if image_base64:
                store_chunk_image(doc.kb_id, chunck_id, base64.b64decode(image_base64))

            DocumentService.increment_chunk_num(
                doc.id, doc.kb_id, c, 1, 0)
            resp = get_json_result(data={"chunk_id": chunck_id, "image_id": d.get("img_id", "")})
            _log_response(resp, RetCode.SUCCESS, "success")
            return resp
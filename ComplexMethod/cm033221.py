def init_llm_factory():
    LLMFactoriesService.filter_delete([1 == 1])
    factory_llm_infos = settings.FACTORY_LLM_INFOS
    for factory_llm_info in factory_llm_infos:
        info = deepcopy(factory_llm_info)
        llm_infos = info.pop("llm")
        try:
            LLMFactoriesService.save(**info)
        except Exception:
            pass
        LLMService.filter_delete([LLM.fid == factory_llm_info["name"]])
        for llm_info in llm_infos:
            llm_info["fid"] = factory_llm_info["name"]
            try:
                LLMService.save(**llm_info)
            except Exception:
                pass

    LLMFactoriesService.filter_delete([(LLMFactories.name == "Local") | (LLMFactories.name == "novita.ai")])
    LLMService.filter_delete([LLM.fid == "Local"])
    LLMService.filter_delete([LLM.llm_name == "qwen-vl-max"])
    LLMService.filter_delete([LLM.fid == "Moonshot", LLM.llm_name == "flag-embedding"])
    TenantLLMService.filter_delete([TenantLLM.llm_factory == "Moonshot", TenantLLM.llm_name == "flag-embedding"])
    LLMFactoriesService.filter_delete([LLMFactoriesService.model.name == "QAnything"])
    LLMService.filter_delete([LLMService.model.fid == "QAnything"])
    TenantLLMService.filter_update([TenantLLMService.model.llm_factory == "QAnything"], {"llm_factory": "Youdao"})
    TenantLLMService.filter_update([TenantLLMService.model.llm_factory == "cohere"], {"llm_factory": "Cohere"})
    TenantService.filter_update([1 == 1], {
        "parser_ids": "naive:General,qa:Q&A,resume:Resume,manual:Manual,table:Table,paper:Paper,book:Book,laws:Laws,presentation:Presentation,picture:Picture,one:One,audio:Audio,email:Email,tag:Tag"})
    ## insert openai two embedding models to the current openai user.
    # print("Start to insert 2 OpenAI embedding models...")
    tenant_ids = set([row["tenant_id"] for row in TenantLLMService.get_openai_models()])
    for tid in tenant_ids:
        for row in TenantLLMService.query(llm_factory="OpenAI", tenant_id=tid):
            row = row.to_dict()
            row["model_type"] = LLMType.EMBEDDING.value
            row["llm_name"] = "text-embedding-3-small"
            row["used_tokens"] = 0
            try:
                TenantLLMService.save(**row)
                row = deepcopy(row)
                row["llm_name"] = "text-embedding-3-large"
                TenantLLMService.save(**row)
            except Exception:
                pass
            break
    doc_count = DocumentService.get_all_kb_doc_count()
    for kb_id in KnowledgebaseService.get_all_ids():
        KnowledgebaseService.update_document_number_in_init(kb_id=kb_id, doc_num=doc_count.get(kb_id, 0))
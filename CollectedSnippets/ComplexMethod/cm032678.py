async def retrieval(self, question: str,
               tenant_ids: str | list[str],
               kb_ids: list[str],
               emb_mdl,
               llm,
               max_token: int = 8196,
               ent_topn: int = 6,
               rel_topn: int = 6,
               comm_topn: int = 1,
               ent_sim_threshold: float = 0.3,
               rel_sim_threshold: float = 0.3,
                  **kwargs
               ):
        qst = question
        filters = self.get_filters({"kb_ids": kb_ids})
        if isinstance(tenant_ids, str):
            tenant_ids = tenant_ids.split(",")
        idxnms = [index_name(tid) for tid in tenant_ids]
        ty_kwds = []
        try:
            ty_kwds, ents = await self.query_rewrite(llm, qst, [index_name(tid) for tid in tenant_ids], kb_ids)
            logging.info(f"Q: {qst}, Types: {ty_kwds}, Entities: {ents}")
        except Exception as e:
            logging.exception(e)
            ents = [qst]
            pass

        ents_from_query = self.get_relevant_ents_by_keywords(ents, filters, idxnms, kb_ids, emb_mdl, ent_sim_threshold)
        ents_from_types = self.get_relevant_ents_by_types(ty_kwds, filters, idxnms, kb_ids, 10000)
        rels_from_txt = self.get_relevant_relations_by_txt(qst, filters, idxnms, kb_ids, emb_mdl, rel_sim_threshold)
        nhop_pathes = defaultdict(dict)
        for _, ent in ents_from_query.items():
            nhops = ent.get("n_hop_ents", [])
            if not isinstance(nhops, list):
                logging.warning(f"Abnormal n_hop_ents: {nhops}")
                continue
            for nbr in nhops:
                path = nbr["path"]
                wts = nbr["weights"]
                for i in range(len(path) - 1):
                    f, t = path[i], path[i + 1]
                    if (f, t) in nhop_pathes:
                        nhop_pathes[(f, t)]["sim"] += ent["sim"] / (2 + i)
                    else:
                        nhop_pathes[(f, t)]["sim"] = ent["sim"] / (2 + i)
                    nhop_pathes[(f, t)]["pagerank"] = wts[i]

        logging.info("Retrieved entities: {}".format(list(ents_from_query.keys())))
        logging.info("Retrieved relations: {}".format(list(rels_from_txt.keys())))
        logging.info("Retrieved entities from types({}): {}".format(ty_kwds, list(ents_from_types.keys())))
        logging.info("Retrieved N-hops: {}".format(list(nhop_pathes.keys())))

        # P(E|Q) => P(E) * P(Q|E) => pagerank * sim
        for ent in ents_from_types.keys():
            if ent not in ents_from_query:
                continue
            ents_from_query[ent]["sim"] *= 2

        for (f, t) in rels_from_txt.keys():
            pair = tuple(sorted([f, t]))
            s = 0
            if pair in nhop_pathes:
                s += nhop_pathes[pair]["sim"]
                del nhop_pathes[pair]
            if f in ents_from_types:
                s += 1
            if t in ents_from_types:
                s += 1
            rels_from_txt[(f, t)]["sim"] *= s + 1

        # This is for the relations from n-hop but not by query search
        for (f, t) in nhop_pathes.keys():
            s = 0
            if f in ents_from_types:
                s += 1
            if t in ents_from_types:
                s += 1
            rels_from_txt[(f, t)] = {
                "sim": nhop_pathes[(f, t)]["sim"] * (s + 1),
                "pagerank": nhop_pathes[(f, t)]["pagerank"]
            }

        ents_from_query = sorted(ents_from_query.items(), key=lambda x: x[1]["sim"] * x[1]["pagerank"], reverse=True)[
                          :ent_topn]
        rels_from_txt = sorted(rels_from_txt.items(), key=lambda x: x[1]["sim"] * x[1]["pagerank"], reverse=True)[
                        :rel_topn]

        ents = []
        relas = []
        for n, ent in ents_from_query:
            ents.append({
                "Entity": n,
                "Score": "%.2f" % (ent["sim"] * ent["pagerank"]),
                "Description": json.loads(ent["description"]).get("description", "") if ent["description"] else ""
            })
            max_token -= num_tokens_from_string(str(ents[-1]))
            if max_token <= 0:
                ents = ents[:-1]
                break

        for (f, t), rel in rels_from_txt:
            if not rel.get("description"):
                for tid in tenant_ids:
                    rela = await get_relation(tid, kb_ids, f, t)
                    if rela:
                        break
                else:
                    continue
                rel["description"] = rela["description"]
            desc = rel["description"]
            try:
                desc = json.loads(desc).get("description", "")
            except Exception:
                pass
            relas.append({
                "From Entity": f,
                "To Entity": t,
                "Score": "%.2f" % (rel["sim"] * rel["pagerank"]),
                "Description": desc
            })
            max_token -= num_tokens_from_string(str(relas[-1]))
            if max_token <= 0:
                relas = relas[:-1]
                break

        if ents:
            ents = "\n---- Entities ----\n{}".format(pd.DataFrame(ents).to_csv())
        else:
            ents = ""
        if relas:
            relas = "\n---- Relations ----\n{}".format(pd.DataFrame(relas).to_csv())
        else:
            relas = ""

        return {
                "chunk_id": get_uuid(),
                "content_ltks": "",
                "content_with_weight": ents + relas + self._community_retrieval_([n for n, _ in ents_from_query], filters, kb_ids, idxnms,
                                                        comm_topn, max_token),
                "doc_id": "",
                "docnm_kwd": "Related content in Knowledge Graph",
                "kb_id": kb_ids,
                "important_kwd": [],
                "image_id": "",
                "similarity": 1.,
                "vector_similarity": 1.,
                "term_similarity": 0,
                "vector": [],
                "positions": [],
            }
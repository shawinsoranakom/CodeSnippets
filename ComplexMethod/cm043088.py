def build_company_graph(companies, embeds:np.ndarray, top_k:int) -> Dict[str,Any]:
    from sklearn.metrics.pairwise import cosine_similarity
    sims = cosine_similarity(embeds)
    nodes, edges = [], []
    for i,c in enumerate(companies):
        node = dict(
            id=c["handle"].strip("/"),
            name=c["name"],
            handle=c["handle"],
            about=c.get("about",""),
            people_url=c.get("people_url",""),
            industry=c.get("descriptor","").split("•")[0].strip(),
            geoUrn=c.get("geoUrn"),
            followers=c.get("followers",0),
            # desc_embed=embeds[i].tolist(),
            desc_embed=[],
        )
        nodes.append(node)
        # pick top-k most similar except itself
        top_idx = np.argsort(sims[i])[::-1][1:top_k+1]
        for j in top_idx:
            tgt = companies[j]
            weight = float(sims[i,j])
            if node["industry"] == tgt.get("descriptor","").split("•")[0].strip():
                weight += 0.10
            if node["geoUrn"] == tgt.get("geoUrn"):
                weight += 0.05
            tgt['followers'] = tgt.get("followers", None) or 1
            node["followers"] = node.get("followers", None) or 1
            follower_ratio = min(node["followers"], tgt.get("followers",1)) / max(node["followers"] or 1, tgt.get("followers",1))
            weight += 0.05 * follower_ratio
            edges.append(dict(
                source=node["id"],
                target=tgt["handle"].strip("/"),
                weight=round(weight,4),
                drivers=dict(
                    embed_sim=round(float(sims[i,j]),4),
                    industry_match=0.10 if node["industry"] == tgt.get("descriptor","").split("•")[0].strip() else 0,
                    geo_overlap=0.05 if node["geoUrn"] == tgt.get("geoUrn") else 0,
                )
            ))
    # return {"nodes":nodes,"edges":edges,"meta":{"generated_at":datetime.now(UTC).isoformat()}}
    return {"nodes":nodes,"edges":edges,"meta":{"generated_at":datetime.now(UTC).isoformat()}}
def update(self, condition: dict, newValue: dict, indexName: str, knowledgebaseId: str) -> bool:
        doc = copy.deepcopy(newValue)
        doc.pop("id", None)
        if "id" in condition and isinstance(condition["id"], str):
            # update specific single document
            chunkId = condition["id"]
            for i in range(ATTEMPT_TIME):
                doc_part = copy.deepcopy(doc)
                remove_value = doc_part.pop("remove", None)
                remove_field = remove_value if isinstance(remove_value, str) else None
                remove_dict = remove_value if isinstance(remove_value, dict) else None
                try:
                    if remove_field is not None:
                        self.os.update(
                            index=indexName,
                            id=chunkId,
                            body={"script": {"source": f"ctx._source.remove('{remove_field}');"}},
                        )
                    if remove_dict is not None:
                        scripts = []
                        params = {}
                        for kk, vv in remove_dict.items():
                            scripts.append(
                                f"if (ctx._source.containsKey('{kk}') && ctx._source.{kk} != null) "
                                f"{{ int i = ctx._source.{kk}.indexOf(params.p_{kk}); "
                                f"if (i >= 0) {{ ctx._source.{kk}.remove(i); }} }}"
                            )
                            params[f"p_{kk}"] = vv
                        if scripts:
                            self.os.update(
                                index=indexName,
                                id=chunkId,
                                body={"script": {"source": "".join(scripts), "params": params}},
                            )
                    if doc_part:
                        self.os.update(index=indexName, id=chunkId, body={"doc": doc_part})
                    if remove_field is not None or remove_dict is not None or doc_part:
                        return True
                except Exception as e:
                    logger.exception(
                        f"OSConnection.update(index={indexName}, id={id}, doc={json.dumps(condition, ensure_ascii=False)}) got exception")
                    if re.search(r"(timeout|connection)", str(e).lower()):
                        continue
                    break
            return False

        # update unspecific maybe-multiple documents
        bqry = Q("bool")
        for k, v in condition.items():
            if not isinstance(k, str) or not v:
                continue
            if k == "exists":
                bqry.filter.append(Q("exists", field=v))
                continue
            if isinstance(v, list):
                bqry.filter.append(Q("terms", **{k: v}))
            elif isinstance(v, str) or isinstance(v, int):
                bqry.filter.append(Q("term", **{k: v}))
            else:
                raise Exception(
                    f"Condition `{str(k)}={str(v)}` value type is {str(type(v))}, expected to be int, str or list.")
        scripts = []
        params = {}
        for k, v in newValue.items():
            if k == "remove":
                if isinstance(v, str):
                    scripts.append(f"ctx._source.remove('{v}');")
                if isinstance(v, dict):
                    for kk, vv in v.items():
                        scripts.append(f"int i=ctx._source.{kk}.indexOf(params.p_{kk});ctx._source.{kk}.remove(i);")
                        params[f"p_{kk}"] = vv
                continue
            if k == "add":
                if isinstance(v, dict):
                    for kk, vv in v.items():
                        scripts.append(f"ctx._source.{kk}.add(params.pp_{kk});")
                        params[f"pp_{kk}"] = vv.strip()
                continue
            if (not isinstance(k, str) or not v) and k != "available_int":
                continue
            if isinstance(v, str):
                v = re.sub(r"(['\n\r]|\\.)", " ", v)
                params[f"pp_{k}"] = v
                scripts.append(f"ctx._source.{k}=params.pp_{k};")
            elif isinstance(v, int) or isinstance(v, float):
                scripts.append(f"ctx._source.{k}={v};")
            elif isinstance(v, list):
                scripts.append(f"ctx._source.{k}=params.pp_{k};")
                params[f"pp_{k}"] = json.dumps(v, ensure_ascii=False)
            else:
                raise Exception(
                    f"newValue `{str(k)}={str(v)}` value type is {str(type(v))}, expected to be int, str.")
        ubq = UpdateByQuery(
            index=indexName).using(
            self.os).query(bqry)
        ubq = ubq.script(source="".join(scripts), params=params)
        ubq = ubq.params(refresh=True)
        ubq = ubq.params(slices=5)
        ubq = ubq.params(conflicts="proceed")

        for _ in range(ATTEMPT_TIME):
            try:
                _ = ubq.execute()
                return True
            except Exception as e:
                logger.error("OSConnection.update got exception: " + str(e) + "\n".join(scripts))
                if re.search(r"(timeout|connection|conflict)", str(e).lower()):
                    continue
                break
        return False
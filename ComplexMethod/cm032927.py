def update(self, condition: dict, new_value: dict, index_name: str, knowledgebase_id: str) -> bool:
        doc = copy.deepcopy(new_value)
        doc.pop("id", None)
        condition["kb_id"] = knowledgebase_id
        if "id" in condition and isinstance(condition["id"], str):
            # update specific single document
            chunk_id = condition["id"]
            for i in range(ATTEMPT_TIME):
                doc_part = copy.deepcopy(doc)
                remove_value = doc_part.pop("remove", None)
                remove_field = remove_value if isinstance(remove_value, str) else None
                remove_dict = remove_value if isinstance(remove_value, dict) else None
                for k in doc_part.keys():
                    if "feas" != k.split("_")[-1]:
                        continue
                    try:
                        self.es.update(index=index_name, id=chunk_id, script=f"ctx._source.remove(\"{k}\");")
                    except Exception:
                        self.logger.exception(
                            f"ESConnection.update(index={index_name}, id={chunk_id}, doc={json.dumps(condition, ensure_ascii=False)}) got exception")
                try:
                    if remove_field is not None:
                        self.es.update(
                            index=index_name,
                            id=chunk_id,
                            script=f"ctx._source.remove('{remove_field}');",
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
                            self.es.update(
                                index=index_name,
                                id=chunk_id,
                                script={"source": "".join(scripts), "params": params},
                            )
                    if doc_part:
                        self.es.update(index=index_name, id=chunk_id, doc=doc_part)
                    if remove_field is not None or remove_dict is not None or doc_part:
                        return True
                except Exception as e:
                    self.logger.exception(
                        f"ESConnection.update(index={index_name}, id={chunk_id}, doc={json.dumps(condition, ensure_ascii=False)}) got exception: " + str(
                            e))
                    break
            return False

        # update unspecific maybe-multiple documents
        bool_query = Q("bool")
        for k, v in condition.items():
            if not isinstance(k, str) or not v:
                continue
            if k == "exists":
                bool_query.filter.append(Q("exists", field=v))
                continue
            if isinstance(v, list):
                bool_query.filter.append(Q("terms", **{k: v}))
            elif isinstance(v, str) or isinstance(v, int):
                bool_query.filter.append(Q("term", **{k: v}))
            else:
                raise Exception(
                    f"Condition `{str(k)}={str(v)}` value type is {str(type(v))}, expected to be int, str or list.")
        scripts = []
        params = {}
        for k, v in new_value.items():
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
            index=index_name).using(
            self.es).query(bool_query)
        ubq = ubq.script(source="".join(scripts), params=params)
        ubq = ubq.params(refresh=True)
        ubq = ubq.params(slices=5)
        ubq = ubq.params(conflicts="proceed")

        for _ in range(ATTEMPT_TIME):
            try:
                _ = ubq.execute()
                return True
            except ConnectionTimeout:
                self.logger.exception("ES request timeout")
                time.sleep(3)
                self._connect()
                continue
            except Exception as e:
                self.logger.error("ESConnection.update got exception: " + str(e) + "\n".join(scripts))
                break
        return False
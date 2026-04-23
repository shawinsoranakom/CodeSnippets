async def extract_community_report(community):
            nonlocal res_str, res_dict, over, token_count
            if task_id:
                if has_canceled(task_id):
                    logging.info(f"Task {task_id} cancelled during community report extraction.")
                    raise TaskCanceledException(f"Task {task_id} was cancelled")

            cm_id, cm = community
            weight = cm["weight"]
            ents = cm["nodes"]
            if len(ents) < 2:
                return
            ent_list = [{"entity": ent, "description": graph.nodes[ent]["description"]} for ent in ents]
            ent_df = pd.DataFrame(ent_list)

            rela_list = []
            k = 0
            for i in range(0, len(ents)):
                if k >= 10000:
                    break
                for j in range(i + 1, len(ents)):
                    if k >= 10000:
                        break
                    edge = graph.get_edge_data(ents[i], ents[j])
                    if edge is None:
                        continue
                    rela_list.append({"source": ents[i], "target": ents[j], "description": edge["description"]})
                    k += 1
            rela_df = pd.DataFrame(rela_list)

            prompt_variables = {
                "entity_df": ent_df.to_csv(index_label="id"),
                "relation_df": rela_df.to_csv(index_label="id")
            }
            text = perform_variable_replacements(self._extraction_prompt, variables=prompt_variables)
            async with chat_limiter:
                try:
                    timeout = 180 if enable_timeout_assertion else 1000000000
                    response = await asyncio.wait_for(self._async_chat(text, [{"role": "user", "content": "Output:"}], {}, task_id), timeout=timeout)
                except asyncio.TimeoutError:
                    logging.warning("extract_community_report._async_chat timeout, skipping...")
                    return
                except Exception as e:
                    logging.error(f"extract_community_report._async_chat failed: {e}")
                    return
            token_count += num_tokens_from_string(text + response)
            response = re.sub(r"^[^\{]*", "", response)
            response = re.sub(r"[^\}]*$", "", response)
            response = re.sub(r"\{\{", "{", response)
            response = re.sub(r"\}\}", "}", response)
            logging.debug(response)
            try:
                response = json.loads(response)
            except json.JSONDecodeError as e:
                logging.error(f"Failed to parse JSON response: {e}")
                logging.error(f"Response content: {response}")
                return
            if not dict_has_keys_with_types(response, [
                        ("title", str),
                        ("summary", str),
                        ("findings", list),
                        ("rating", float),
                        ("rating_explanation", str),
                    ]):
                return
            response["weight"] = weight
            response["entities"] = ents
            add_community_info2graph(graph, ents, response["title"])
            res_str.append(self._get_text_output(response))
            res_dict.append(response)
            over += 1
            if callback:
                callback(msg=f"Communities: {over}/{total}, used tokens: {token_count}")
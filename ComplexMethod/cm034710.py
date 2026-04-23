async def iter_messages_line(cls, session: StreamSession, auth_result: AuthResult, line: bytes,
                                 fields: Conversation, sources: OpenAISources,
                                 references: ContentReferences) -> AsyncIterator:
        if not line.startswith(b"data: "):
            return
        elif line.startswith(b"data: [DONE]"):
            return
        try:
            line = json.loads(line[6:])
        except Exception:
            return
        if not isinstance(line, dict):
            return
        if "type" in line:
            if line["type"] == "title_generation":
                yield TitleGeneration(line["title"])
        fields.p = line.get("p", fields.p)
        if fields.p is not None and fields.p.startswith("/message/content/thoughts"):
            if fields.p.endswith("/content"):
                if fields.thoughts_summary:
                    yield Reasoning(token="", status=fields.thoughts_summary)
                    fields.thoughts_summary = ""
                yield Reasoning(token=line.get("v"))
            elif fields.p.endswith("/summary"):
                fields.thoughts_summary += line.get("v")
            return
        if "v" in line:
            v = line.get("v")
            if isinstance(v, str) and fields.recipient == "all":
                if fields.p == "/message/metadata/refresh_key_info":
                    yield ""
                elif "p" not in line or line.get("p") == "/message/content/parts/0":
                    yield Reasoning(token=v) if fields.is_thinking else v
            elif isinstance(v, list):
                buffer = ""
                for m in v:
                    if m.get("p") == "/message/content/parts/0" and fields.recipient == "all":
                        buffer += m.get("v")
                    elif m.get("p") == "/message/metadata/image_gen_title":
                        fields.prompt = m.get("v")
                    elif m.get("p") == "/message/content/parts/0/asset_pointer":
                        status = next(filter(lambda x: x.get("p") == '/message/status', v), {}).get('v', None)
                        generated_images = fields.generated_images = await cls.get_generated_image(session, auth_result,
                                                                                                   m.get("v"),
                                                                                                   fields.prompt,
                                                                                                   fields.conversation_id,
                                                                                                   status)
                        if generated_images is not None:
                            if buffer:
                                yield buffer
                            yield generated_images
                    elif m.get("p") == "/message/metadata/search_result_groups":
                        for entry in [p.get("entries") for p in m.get("v")]:
                            for link in entry:
                                sources.add_source(link)
                    elif m.get("p") == "/message/metadata/content_references" and not isinstance(m.get("v"), int):
                        for entry in m.get("v"):
                            for link in entry.get("sources", []):
                                sources.add_source(link)
                            for link in entry.get("items", []):
                                sources.add_source(link)
                            for link in entry.get("fallback_items", []) or []:
                                sources.add_source(link)
                            if m.get("o", None) == "append":
                                references.add_reference(entry)
                    elif m.get("p") and re.match(r"^/message/metadata/content_references/\d+$", m.get("p")):
                        if "url" in m.get("v") or "link" in m.get("v"):
                            sources.add_source(m.get("v"))
                        for link in m.get("v").get("fallback_items", []) or []:
                            sources.add_source(link)

                        match = re.match(r"^/message/metadata/content_references/(\d+)$", m.get("p"))
                        if match and m.get("o") == "append" and isinstance(m.get("v"), dict):
                            idx = int(match.group(1))
                            references.merge_reference(idx, m.get("v"))
                    elif m.get("p") and re.match(r"^/message/metadata/content_references/\d+/fallback_items$",
                                                 m.get("p")) and isinstance(m.get("v"), list):
                        for link in m.get("v", []) or []:
                            sources.add_source(link)
                    elif m.get("p") and re.match(r"^/message/metadata/content_references/\d+/items$",
                                                 m.get("p")) and isinstance(m.get("v"), list):
                        for link in m.get("v", []) or []:
                            sources.add_source(link)
                    elif m.get("p") and re.match(r"^/message/metadata/content_references/\d+/refs$",
                                                 m.get("p")) and isinstance(m.get("v"), list):
                        match = re.match(r"^/message/metadata/content_references/(\d+)/refs$", m.get("p"))
                        if match:
                            idx = int(match.group(1))
                            references.update_reference(idx, m.get("o"), "refs", m.get("v"))
                    elif m.get("p") and re.match(r"^/message/metadata/content_references/\d+/alt$",
                                                 m.get("p")) and isinstance(m.get("v"), list):
                        match = re.match(r"^/message/metadata/content_references/(\d+)/alt$", m.get("p"))
                        if match:
                            idx = int(match.group(1))
                            references.update_reference(idx, m.get("o"), "alt", m.get("v"))
                    elif m.get("p") and re.match(r"^/message/metadata/content_references/\d+/prompt_text$",
                                                 m.get("p")) and isinstance(m.get("v"), list):
                        match = re.match(r"^/message/metadata/content_references/(\d+)/prompt_text$", m.get("p"))
                        if match:
                            idx = int(match.group(1))
                            references.update_reference(idx, m.get("o"), "prompt_text", m.get("v"))
                    elif m.get("p") and re.match(r"^/message/metadata/content_references/\d+/refs/\d+$",
                                                 m.get("p")) and isinstance(m.get("v"), dict):
                        match = re.match(r"^/message/metadata/content_references/(\d+)/refs/(\d+)$", m.get("p"))
                        if match:
                            reference_idx = int(match.group(1))
                            ref_idx = int(match.group(2))
                            references.update_reference(reference_idx, m.get("o"), "refs", m.get("v"), ref_idx)
                    elif m.get("p") and re.match(r"^/message/metadata/content_references/\d+/images$",
                                                 m.get("p")) and isinstance(m.get("v"), list):
                        match = re.match(r"^/message/metadata/content_references/(\d+)/images$", m.get("p"))
                        if match:
                            idx = int(match.group(1))
                            references.update_reference(idx, m.get("o"), "images", m.get("v"))
                    elif m.get("p") == "/message/metadata/finished_text":
                        fields.is_thinking = False
                        if buffer:
                            yield buffer
                        yield Reasoning(status=m.get("v"))
                    elif m.get("p") == "/message/metadata" and fields.recipient == "all":
                        fields.finish_reason = m.get("v", {}).get("finish_details", {}).get("type")
                        break

                yield buffer
            elif isinstance(v, dict):
                if fields.conversation_id is None:
                    fields.conversation_id = v.get("conversation_id")
                    debug.log(f"OpenaiChat: New conversation: {fields.conversation_id}")
                m = v.get("message", {})
                fields.recipient = m.get("recipient", fields.recipient)
                if fields.recipient == "all":
                    c = m.get("content", {})
                    if c.get("content_type") == "text" and m.get("author", {}).get(
                            "role") == "tool" and "initial_text" in m.get("metadata", {}):
                        fields.is_thinking = True
                        yield Reasoning(status=m.get("metadata", {}).get("initial_text"))
                    # if c.get("content_type") == "multimodal_text":
                    #    for part in c.get("parts"):
                    #        if isinstance(part, dict) and part.get("content_type") == "image_asset_pointer":
                    #            yield await cls.get_generated_image(session, auth_result, part, fields.prompt, fields.conversation_id)
                    if m.get("author", {}).get("role") == "assistant":
                        if fields.parent_message_id is None:
                            fields.parent_message_id = v.get("message", {}).get("id")
                        fields.message_id = v.get("message", {}).get("id")
                    if m.get("status") == "finished_successfully" and m.get("metadata", {}).get("image_gen_task_id"):
                        fields.task = v
            return
        if "error" in line and line.get("error"):
            raise RuntimeError(line.get("error"))
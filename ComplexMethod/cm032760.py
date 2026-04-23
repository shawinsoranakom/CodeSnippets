def build_chunks(self, line_records, resolved):
        target_level = _resolve_group_target_level(
            resolved["levels"],
            self.param.hierarchy,
            resolved["most_level"],
        )
        sec_ids = _build_section_ids(resolved["levels"], target_level)
        record_groups = []
        tk_cnt = 0
        last_sid = -2

        # The merge state is driven by (current section id, current token size).
        # A chunk stays open while records remain in the same logical section,
        # except that very small chunks are allowed to absorb the next record
        # regardless of section change.
        for record, sec_id in zip(line_records, sec_ids):
            if record["doc_type_kwd"] != "text":
                record_groups.append([record])
                tk_cnt = 0
                last_sid = -2
                continue

            text = record["text"]
            if not text.strip():
                continue

            token_count = num_tokens_from_string(text)
            should_merge = (
                record_groups
                and record_groups[-1][0]["doc_type_kwd"] == "text"
                and (
                    tk_cnt < MIN_GROUP_TOKENS
                    or (tk_cnt < MAX_GROUP_TOKENS and sec_id == last_sid)
                )
            )

            if should_merge:
                record_groups[-1].append(record)
                tk_cnt += token_count
            else:
                record_groups.append([record])
                tk_cnt = token_count

            last_sid = sec_id

        return self.build_chunks_from_record_groups(record_groups)
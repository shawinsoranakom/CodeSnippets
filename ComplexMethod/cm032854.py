def attach_media_context(chunks, table_context_size=0, image_context_size=0):
    """
    Attach surrounding text chunk content to media chunks (table/image).
    Best-effort ordering: if positional info exists on any chunk, use it to
    order chunks before collecting context; otherwise keep original order.
    """
    from . import rag_tokenizer

    if not chunks or (table_context_size <= 0 and image_context_size <= 0):
        return chunks

    def is_image_chunk(ck):
        if ck.get("doc_type_kwd") == "image":
            return True

        text_val = ck.get("content_with_weight") if isinstance(ck.get("content_with_weight"), str) else ck.get("text")
        has_text = isinstance(text_val, str) and text_val.strip()
        return bool(ck.get("image")) and not has_text

    def is_table_chunk(ck):
        return ck.get("doc_type_kwd") == "table"

    def is_text_chunk(ck):
        return not is_image_chunk(ck) and not is_table_chunk(ck)

    def get_text(ck):
        if isinstance(ck.get("content_with_weight"), str):
            return ck["content_with_weight"]
        if isinstance(ck.get("text"), str):
            return ck["text"]
        return ""

    def split_sentences(text):
        pattern = r"([.。！？!?；;：:\n])"
        parts = re.split(pattern, text)
        sentences = []
        buf = ""
        for p in parts:
            if not p:
                continue
            if re.fullmatch(pattern, p):
                buf += p
                sentences.append(buf)
                buf = ""
            else:
                buf += p
        if buf:
            sentences.append(buf)
        return sentences

    def get_bounds_by_page(ck):
        bounds = {}
        try:
            if ck.get("position_int"):
                for pos in ck["position_int"]:
                    if not pos or len(pos) < 5:
                        continue
                    pn, _, _, top, bottom = pos
                    if pn is None or top is None:
                        continue
                    top_val = float(top)
                    bottom_val = float(bottom) if bottom is not None else top_val
                    if bottom_val < top_val:
                        top_val, bottom_val = bottom_val, top_val
                    pn = int(pn)
                    if pn in bounds:
                        bounds[pn] = (min(bounds[pn][0], top_val), max(bounds[pn][1], bottom_val))
                    else:
                        bounds[pn] = (top_val, bottom_val)
            else:
                pn = None
                if ck.get("page_num_int"):
                    pn = ck["page_num_int"][0]
                elif ck.get("page_number") is not None:
                    pn = ck.get("page_number")
                if pn is None:
                    return bounds
                top = None
                if ck.get("top_int"):
                    top = ck["top_int"][0]
                elif ck.get("top") is not None:
                    top = ck.get("top")
                if top is None:
                    return bounds
                bottom = ck.get("bottom")
                pn = int(pn)
                top_val = float(top)
                bottom_val = float(bottom) if bottom is not None else top_val
                if bottom_val < top_val:
                    top_val, bottom_val = bottom_val, top_val
                bounds[pn] = (top_val, bottom_val)
        except Exception:
            return {}
        return bounds

    def trim_to_tokens(text, token_budget, from_tail=False):
        if token_budget <= 0 or not text:
            return ""
        sentences = split_sentences(text)
        if not sentences:
            return ""

        collected = []
        remaining = token_budget
        seq = reversed(sentences) if from_tail else sentences
        for s in seq:
            tks = num_tokens_from_string(s)
            if tks <= 0:
                continue
            if tks > remaining:
                collected.append(s)
                break
            collected.append(s)
            remaining -= tks

        if from_tail:
            collected = list(reversed(collected))
        return "".join(collected)

    def find_mid_sentence_index(sentences):
        if not sentences:
            return 0
        total = sum(max(0, num_tokens_from_string(s)) for s in sentences)
        if total <= 0:
            return max(0, len(sentences) // 2)
        target = total / 2.0
        best_idx = 0
        best_diff = None
        cum = 0
        for i, s in enumerate(sentences):
            cum += max(0, num_tokens_from_string(s))
            diff = abs(cum - target)
            if best_diff is None or diff < best_diff:
                best_diff = diff
                best_idx = i
        return best_idx

    def collect_context_from_sentences(sentences, boundary_idx, token_budget):
        prev_ctx = []
        remaining_prev = token_budget
        for s in reversed(sentences[:boundary_idx + 1]):
            if remaining_prev <= 0:
                break
            tks = num_tokens_from_string(s)
            if tks <= 0:
                continue
            if tks > remaining_prev:
                s = trim_to_tokens(s, remaining_prev, from_tail=True)
                tks = num_tokens_from_string(s)
            prev_ctx.append(s)
            remaining_prev -= tks
        prev_ctx.reverse()

        next_ctx = []
        remaining_next = token_budget
        for s in sentences[boundary_idx + 1:]:
            if remaining_next <= 0:
                break
            tks = num_tokens_from_string(s)
            if tks <= 0:
                continue
            if tks > remaining_next:
                s = trim_to_tokens(s, remaining_next, from_tail=False)
                tks = num_tokens_from_string(s)
            next_ctx.append(s)
            remaining_next -= tks
        return prev_ctx, next_ctx

    def extract_position(ck):
        pn = None
        top = None
        left = None
        try:
            if ck.get("page_num_int"):
                pn = ck["page_num_int"][0]
            elif ck.get("page_number") is not None:
                pn = ck.get("page_number")

            if ck.get("top_int"):
                top = ck["top_int"][0]
            elif ck.get("top") is not None:
                top = ck.get("top")

            if ck.get("position_int"):
                left = ck["position_int"][0][1]
            elif ck.get("x0") is not None:
                left = ck.get("x0")
        except Exception:
            pn = top = left = None
        return pn, top, left

    indexed = list(enumerate(chunks))
    positioned_indices = []
    unpositioned_indices = []
    for idx, ck in indexed:
        pn, top, left = extract_position(ck)
        if pn is not None and top is not None:
            positioned_indices.append((idx, pn, top, left if left is not None else 0))
        else:
            unpositioned_indices.append(idx)

    if positioned_indices:
        positioned_indices.sort(key=lambda x: (int(x[1]), int(x[2]), int(x[3]), x[0]))
        ordered_indices = [i for i, _, _, _ in positioned_indices] + unpositioned_indices
    else:
        ordered_indices = [idx for idx, _ in indexed]

    text_bounds = []
    for idx, ck in indexed:
        if not is_text_chunk(ck):
            continue
        bounds = get_bounds_by_page(ck)
        if bounds:
            text_bounds.append((idx, bounds))

    for sorted_pos, idx in enumerate(ordered_indices):
        ck = chunks[idx]
        token_budget = image_context_size if is_image_chunk(ck) else table_context_size if is_table_chunk(ck) else 0
        if token_budget <= 0:
            continue

        prev_ctx = []
        next_ctx = []
        media_bounds = get_bounds_by_page(ck)
        best_idx = None
        best_dist = None
        candidate_count = 0
        if media_bounds and text_bounds:
            for text_idx, bounds in text_bounds:
                for pn, (t_top, t_bottom) in bounds.items():
                    if pn not in media_bounds:
                        continue
                    m_top, m_bottom = media_bounds[pn]
                    if m_bottom < t_top or m_top > t_bottom:
                        continue
                    candidate_count += 1
                    m_mid = (m_top + m_bottom) / 2.0
                    t_mid = (t_top + t_bottom) / 2.0
                    dist = abs(m_mid - t_mid)
                    if best_dist is None or dist < best_dist:
                        best_dist = dist
                        best_idx = text_idx
        if best_idx is None and media_bounds:
            media_page = min(media_bounds.keys())
            page_order = []
            for ordered_idx in ordered_indices:
                pn, _, _ = extract_position(chunks[ordered_idx])
                if pn == media_page:
                    page_order.append(ordered_idx)
            if page_order and idx in page_order:
                pos_in_page = page_order.index(idx)
                if pos_in_page == 0:
                    for neighbor in page_order[pos_in_page + 1:]:
                        if is_text_chunk(chunks[neighbor]):
                            best_idx = neighbor
                            break
                elif pos_in_page == len(page_order) - 1:
                    for neighbor in reversed(page_order[:pos_in_page]):
                        if is_text_chunk(chunks[neighbor]):
                            best_idx = neighbor
                            break
        if best_idx is not None:
            base_text = get_text(chunks[best_idx])
            sentences = split_sentences(base_text)
            if sentences:
                boundary_idx = find_mid_sentence_index(sentences)
                prev_ctx, next_ctx = collect_context_from_sentences(sentences, boundary_idx, token_budget)

        if not prev_ctx and not next_ctx:
            continue

        self_text = get_text(ck)
        pieces = [*prev_ctx]
        if self_text:
            pieces.append(self_text)
        pieces.extend(next_ctx)
        combined = "\n".join(pieces)

        original = ck.get("content_with_weight")
        if "content_with_weight" in ck:
            ck["content_with_weight"] = combined
        elif "text" in ck:
            original = ck.get("text")
            ck["text"] = combined

        if combined != original:
            if "content_ltks" in ck:
                ck["content_ltks"] = rag_tokenizer.tokenize(combined)
            if "content_sm_ltks" in ck:
                ck["content_sm_ltks"] = rag_tokenizer.fine_grained_tokenize(
                    ck.get("content_ltks", rag_tokenizer.tokenize(combined)))

    if positioned_indices:
        chunks[:] = [chunks[i] for i in ordered_indices]

    return chunks
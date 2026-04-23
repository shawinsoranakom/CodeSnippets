def chunk_markdown_by_structure(
	content: str,
	max_chunk_chars: int = 100_000,
	overlap_lines: int = 5,
	start_from_char: int = 0,
) -> list[MarkdownChunk]:
	"""Split markdown into structure-aware chunks.

	Algorithm:
	  Phase 1 — Parse atomic blocks (headers, code fences, tables, list items, paragraphs).
	  Phase 2 — Greedy chunk assembly: accumulate blocks until exceeding max_chunk_chars.
	            A single block exceeding the limit is allowed (soft limit).
	  Phase 3 — Build overlap prefixes for context carry between chunks.

	Args:
	    content: Full markdown string.
	    max_chunk_chars: Target maximum chars per chunk (soft limit for single blocks).
	    overlap_lines: Number of trailing lines from previous chunk to prepend.
	    start_from_char: Return chunks starting from the chunk that contains this offset.

	Returns:
	    List of MarkdownChunk. Empty if start_from_char is past end of content.
	"""
	if not content:
		return [
			MarkdownChunk(
				content='',
				chunk_index=0,
				total_chunks=1,
				char_offset_start=0,
				char_offset_end=0,
				overlap_prefix='',
				has_more=False,
			)
		]

	if start_from_char >= len(content):
		return []

	# Phase 1: parse atomic blocks
	blocks = _parse_atomic_blocks(content)
	if not blocks:
		return []

	# Phase 2: greedy chunk assembly with header-preferred splitting
	raw_chunks: list[list[_AtomicBlock]] = []
	current_chunk: list[_AtomicBlock] = []
	current_size = 0

	for block in blocks:
		block_size = block.char_end - block.char_start
		# If adding this block would exceed limit AND we already have content, emit chunk
		if current_size + block_size > max_chunk_chars and current_chunk:
			# Prefer splitting at a header boundary within the current chunk.
			# Scan backwards for the last HEADER block; if found and it wouldn't
			# create a tiny chunk (< 50% of limit), split right before it so the
			# header starts the next chunk for better semantic coherence.
			best_split = len(current_chunk)
			for j in range(len(current_chunk) - 1, 0, -1):
				if current_chunk[j].block_type == _BlockType.HEADER:
					prefix_size = sum(b.char_end - b.char_start for b in current_chunk[:j])
					if prefix_size >= max_chunk_chars * 0.5:
						best_split = j
						break
			raw_chunks.append(current_chunk[:best_split])
			# Carry remaining blocks (from the header onward) into the next chunk
			current_chunk = current_chunk[best_split:]
			current_size = sum(b.char_end - b.char_start for b in current_chunk)
		current_chunk.append(block)
		current_size += block_size

	if current_chunk:
		raw_chunks.append(current_chunk)

	total_chunks = len(raw_chunks)

	# Phase 3: build MarkdownChunk objects with overlap prefixes
	chunks: list[MarkdownChunk] = []
	# Track table header from previous chunk for table continuations
	prev_chunk_last_table_header: str | None = None

	for idx, chunk_blocks in enumerate(raw_chunks):
		chunk_text = '\n'.join(_block_text(b) for b in chunk_blocks)
		char_start = chunk_blocks[0].char_start
		char_end = chunk_blocks[-1].char_end

		# Build overlap prefix
		overlap = ''
		if idx > 0:
			prev_blocks = raw_chunks[idx - 1]
			prev_text = '\n'.join(_block_text(b) for b in prev_blocks)
			prev_lines = prev_text.split('\n')

			# Check if current chunk starts with a table continuation
			first_block = chunk_blocks[0]
			if first_block.block_type == _BlockType.TABLE and prev_chunk_last_table_header:
				# Always prepend table header for continuation
				trailing = prev_lines[-(overlap_lines):] if overlap_lines > 0 else []
				header_lines = prev_chunk_last_table_header.split('\n')
				# Deduplicate: don't repeat header lines if they're already in trailing
				combined = list(header_lines)
				for tl in trailing:
					if tl not in combined:
						combined.append(tl)
				overlap = '\n'.join(combined)
			elif overlap_lines > 0:
				overlap = '\n'.join(prev_lines[-(overlap_lines):])

		# Track table header from this chunk for next iteration.
		# Only overwrite if this chunk contains a new header+separator block;
		# otherwise preserve the previous header so tables spanning 3+ chunks
		# still get the header carried forward.
		for b in chunk_blocks:
			if b.block_type == _BlockType.TABLE:
				hdr = _get_table_header(b)
				if hdr is not None:
					prev_chunk_last_table_header = hdr

		has_more = idx < total_chunks - 1
		chunks.append(
			MarkdownChunk(
				content=chunk_text,
				chunk_index=idx,
				total_chunks=total_chunks,
				char_offset_start=char_start,
				char_offset_end=char_end,
				overlap_prefix=overlap,
				has_more=has_more,
			)
		)

	# Apply start_from_char filter: return chunks from the one containing that offset
	if start_from_char > 0:
		for i, chunk in enumerate(chunks):
			if chunk.char_offset_end > start_from_char:
				return chunks[i:]
		return []  # offset past all chunks

	return chunks
def _parse_atomic_blocks(content: str) -> list[_AtomicBlock]:
	"""Phase 1: Walk lines, group into unsplittable blocks."""
	lines = content.split('\n')
	blocks: list[_AtomicBlock] = []
	i = 0
	offset = 0  # char offset tracking

	while i < len(lines):
		line = lines[i]
		line_len = len(line) + 1  # +1 for the newline we split on

		# BLANK
		if not line.strip():
			blocks.append(
				_AtomicBlock(
					block_type=_BlockType.BLANK,
					lines=[line],
					char_start=offset,
					char_end=offset + line_len,
				)
			)
			offset += line_len
			i += 1
			continue

		# CODE FENCE
		if line.strip().startswith('```'):
			fence_lines = [line]
			fence_end = offset + line_len
			i += 1
			# Consume until closing fence or EOF
			while i < len(lines):
				fence_line = lines[i]
				fence_line_len = len(fence_line) + 1
				fence_lines.append(fence_line)
				fence_end += fence_line_len
				i += 1
				if fence_line.strip().startswith('```') and len(fence_lines) > 1:
					break
			blocks.append(
				_AtomicBlock(
					block_type=_BlockType.CODE_FENCE,
					lines=fence_lines,
					char_start=offset,
					char_end=fence_end,
				)
			)
			offset = fence_end
			continue

		# HEADER
		if line.lstrip().startswith('#'):
			blocks.append(
				_AtomicBlock(
					block_type=_BlockType.HEADER,
					lines=[line],
					char_start=offset,
					char_end=offset + line_len,
				)
			)
			offset += line_len
			i += 1
			continue

		# TABLE (consecutive |...|  lines)
		# Header + separator row stay together; each data row is its own block
		if _TABLE_ROW_RE.match(line):
			# Collect header line
			header_lines = [line]
			header_end = offset + line_len
			i += 1
			# Check if next line is separator (contains ---)
			if i < len(lines) and _TABLE_ROW_RE.match(lines[i]) and '---' in lines[i]:
				sep = lines[i]
				sep_len = len(sep) + 1
				header_lines.append(sep)
				header_end += sep_len
				i += 1
			# Emit header+separator as one atomic block
			blocks.append(
				_AtomicBlock(
					block_type=_BlockType.TABLE,
					lines=header_lines,
					char_start=offset,
					char_end=header_end,
				)
			)
			offset = header_end
			# Each subsequent table row is its own TABLE block (splittable between rows)
			while i < len(lines) and _TABLE_ROW_RE.match(lines[i]):
				row = lines[i]
				row_len = len(row) + 1
				blocks.append(
					_AtomicBlock(
						block_type=_BlockType.TABLE,
						lines=[row],
						char_start=offset,
						char_end=offset + row_len,
					)
				)
				offset += row_len
				i += 1
			continue

		# LIST ITEM (with indented continuations)
		if _LIST_ITEM_RE.match(line):
			list_lines = [line]
			list_end = offset + line_len
			i += 1
			# Consume continuation lines (indented or blank between items)
			while i < len(lines):
				next_line = lines[i]
				next_len = len(next_line) + 1
				# Another list item at same or deeper indent → still part of this block
				if _LIST_ITEM_RE.match(next_line):
					list_lines.append(next_line)
					list_end += next_len
					i += 1
					continue
				# Indented continuation
				if next_line.strip() and _LIST_CONTINUATION_RE.match(next_line):
					list_lines.append(next_line)
					list_end += next_len
					i += 1
					continue
				break
			blocks.append(
				_AtomicBlock(
					block_type=_BlockType.LIST_ITEM,
					lines=list_lines,
					char_start=offset,
					char_end=list_end,
				)
			)
			offset = list_end
			continue

		# PARAGRAPH (everything else, up to next blank line)
		para_lines = [line]
		para_end = offset + line_len
		i += 1
		while i < len(lines) and lines[i].strip():
			# Stop if next line starts a different block type
			nl = lines[i]
			if nl.lstrip().startswith('#') or nl.strip().startswith('```') or _TABLE_ROW_RE.match(nl) or _LIST_ITEM_RE.match(nl):
				break
			nl_len = len(nl) + 1
			para_lines.append(nl)
			para_end += nl_len
			i += 1
		blocks.append(
			_AtomicBlock(
				block_type=_BlockType.PARAGRAPH,
				lines=para_lines,
				char_start=offset,
				char_end=para_end,
			)
		)
		offset = para_end

	# Fix last block char_end: content may not end with \n
	if blocks and content and not content.endswith('\n'):
		blocks[-1] = _AtomicBlock(
			block_type=blocks[-1].block_type,
			lines=blocks[-1].lines,
			char_start=blocks[-1].char_start,
			char_end=len(content),
		)

	return blocks
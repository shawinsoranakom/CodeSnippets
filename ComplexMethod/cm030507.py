def _render_source_with_highlights(self, line_content: str, line_num: int,
                                        filename: str, bytecode_data: list) -> str:
        """Render source line with instruction highlight spans.

        Simple: collect ranges with sample counts, assign each byte position to
        smallest covering range, then emit spans for contiguous runs with sample data.
        """
        content = line_content.rstrip('\n')
        if not content:
            return ''

        # Collect all (start, end) -> {samples, opcodes} mapping from instructions
        # Multiple instructions may share the same range, so we sum samples and collect opcodes
        range_data = {}
        for instr in bytecode_data:
            samples = instr.get('samples', 0)
            opname = instr.get('opname', '')
            for loc in instr.get('locations', []):
                if loc.get('end_lineno', line_num) == line_num:
                    start, end = loc.get('col_offset', -1), loc.get('end_col_offset', -1)
                    if start >= 0 and end >= 0:
                        key = (start, end)
                        if key not in range_data:
                            range_data[key] = {'samples': 0, 'opcodes': []}
                        range_data[key]['samples'] += samples
                        if opname and opname not in range_data[key]['opcodes']:
                            range_data[key]['opcodes'].append(opname)

        if not range_data:
            return html.escape(content)

        # For each byte position, find the smallest covering range
        byte_to_range = {}
        for (start, end) in range_data.keys():
            for pos in range(start, end):
                if pos not in byte_to_range:
                    byte_to_range[pos] = (start, end)
                else:
                    # Keep smaller range
                    old_start, old_end = byte_to_range[pos]
                    if (end - start) < (old_end - old_start):
                        byte_to_range[pos] = (start, end)

        # Calculate totals for percentage and intensity
        total_line_samples = sum(d['samples'] for d in range_data.values())
        max_range_samples = max(d['samples'] for d in range_data.values()) if range_data else 1

        # Render character by character
        result = []
        byte_offset = 0
        char_idx = 0
        current_range = None
        span_chars = []

        def flush_span():
            nonlocal span_chars, current_range
            if span_chars:
                text = html.escape(''.join(span_chars))
                if current_range:
                    data = range_data.get(current_range, {'samples': 0, 'opcodes': []})
                    samples = data['samples']
                    opcodes = ', '.join(data['opcodes'][:3])  # Top 3 opcodes
                    if len(data['opcodes']) > 3:
                        opcodes += f" +{len(data['opcodes']) - 3} more"
                    pct = int(100 * samples / total_line_samples) if total_line_samples > 0 else 0
                    result.append(f'<span class="instr-span" '
                                  f'data-col-start="{current_range[0]}" '
                                  f'data-col-end="{current_range[1]}" '
                                  f'data-samples="{samples}" '
                                  f'data-max-samples="{max_range_samples}" '
                                  f'data-pct="{pct}" '
                                  f'data-opcodes="{html.escape(opcodes)}">{text}</span>')
                else:
                    result.append(text)
                span_chars = []

        while char_idx < len(content):
            char = content[char_idx]
            char_bytes = len(char.encode('utf-8'))
            char_range = byte_to_range.get(byte_offset)

            if char_range != current_range:
                flush_span()
                current_range = char_range

            span_chars.append(char)
            byte_offset += char_bytes
            char_idx += 1

        flush_span()
        return ''.join(result)
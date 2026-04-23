def test_large_table_produces_valid_chunks(self):
		"""200-row HTML table → markdown → chunks should produce valid table rows in every chunk."""
		rows = ''.join(f'<tr><td>Row {i}</td><td>Val {i}</td></tr>' for i in range(200))
		html = f'<table><thead><tr><th>Name</th><th>Value</th></tr></thead><tbody>{rows}</tbody></table>'
		markdown = md(html, heading_style='ATX')

		chunks = chunk_markdown_by_structure(markdown, max_chunk_chars=500)
		assert len(chunks) > 1, 'Should produce multiple chunks for 200 rows'

		for chunk in chunks:
			lines = chunk.content.strip().split('\n')
			for line in lines:
				s = line.strip()
				if s.startswith('|') and s.endswith('|'):
					# Every table line should have consistent column count
					assert s.count('|') >= 3
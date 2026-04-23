async def test_large_table_extraction_preserves_structure(self, browser_session, httpserver: HTTPServer):
		"""Large table extraction should produce structure-aware chunks."""
		rows = ''.join(f'<tr><td>Name{i}</td><td>Value{i}</td></tr>' for i in range(300))
		html = f"""
		<html><body>
		<table>
			<tr><th>Name</th><th>Value</th></tr>
			{rows}
		</table>
		</body></html>
		"""
		httpserver.expect_request('/big-table').respond_with_data(html, content_type='text/html')
		url = httpserver.url_for('/big-table')

		await browser_session.navigate_to(url)

		from browser_use.dom.markdown_extractor import extract_clean_markdown

		content, _ = await extract_clean_markdown(browser_session=browser_session)

		# Chunk with a small limit to force multiple chunks
		chunks = chunk_markdown_by_structure(content, max_chunk_chars=2000)

		# Should produce multiple chunks
		assert len(chunks) > 1

		# Each chunk should have complete table rows
		for chunk in chunks:
			for line in chunk.content.split('\n'):
				s = line.strip()
				if s.startswith('|') and s.endswith('|'):
					assert s.count('|') >= 3, f'Incomplete table row: {s}'
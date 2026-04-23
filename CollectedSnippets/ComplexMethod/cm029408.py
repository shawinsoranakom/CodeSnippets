async def save_as_pdf(
			params: SaveAsPdfAction,
			browser_session: BrowserSession,
			file_system: FileSystem,
		):
			"""Save the current page as a PDF using CDP Page.printToPDF."""
			import base64
			import re

			# Paper format dimensions in inches (width, height)
			paper_sizes: dict[str, tuple[float, float]] = {
				'letter': (8.5, 11),
				'legal': (8.5, 14),
				'a4': (8.27, 11.69),
				'a3': (11.69, 16.54),
				'tabloid': (11, 17),
			}

			paper_key = params.paper_format.lower()
			if paper_key not in paper_sizes:
				paper_key = 'letter'
			paper_width, paper_height = paper_sizes[paper_key]

			cdp_session = await browser_session.get_or_create_cdp_session(focus=True)

			result = await asyncio.wait_for(
				cdp_session.cdp_client.send.Page.printToPDF(
					params={
						'printBackground': params.print_background,
						'landscape': params.landscape,
						'scale': params.scale,
						'paperWidth': paper_width,
						'paperHeight': paper_height,
						'preferCSSPageSize': True,
					},
					session_id=cdp_session.session_id,
				),
				timeout=30.0,
			)

			pdf_data = result.get('data')
			assert pdf_data, 'CDP Page.printToPDF returned no data'

			pdf_bytes = base64.b64decode(pdf_data)

			# Determine filename
			if params.file_name:
				file_name = params.file_name
			else:
				try:
					page_title = await asyncio.wait_for(browser_session.get_current_page_title(), timeout=2.0)
					safe_title = re.sub(r'[^\w\s-]', '', page_title).strip()[:50]
					file_name = safe_title if safe_title else 'page'
				except Exception:
					file_name = 'page'

			if not file_name.lower().endswith('.pdf'):
				file_name = f'{file_name}.pdf'
			file_name = FileSystem.sanitize_filename(file_name)

			file_path = file_system.get_dir() / file_name
			# Handle duplicate filenames
			if file_path.exists():
				base, ext = os.path.splitext(file_name)
				counter = 1
				while (file_system.get_dir() / f'{base} ({counter}){ext}').exists():
					counter += 1
				file_name = f'{base} ({counter}){ext}'
				file_path = file_system.get_dir() / file_name

			async with await anyio.open_file(file_path, 'wb') as f:
				await f.write(pdf_bytes)

			file_size = file_path.stat().st_size
			msg = f'Saved page as PDF: {file_name} ({file_size:,} bytes)'
			logger.info(f'📄 {msg}. Full path: {file_path}')

			return ActionResult(
				extracted_content=msg,
				long_term_memory=f'{msg}. Full path: {file_path}',
				attachments=[str(file_path)],
			)
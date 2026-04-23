async def extract_latest_article(site_url: str, debug: bool = False) -> dict:
	"""Open site_url, navigate to the newest article and return structured JSON."""

	prompt = (
		f'Navigate to {site_url} and find the most recent headline article (usually at the top). '
		f'Click on it to open the full article page. Once loaded, scroll & extract ALL required information: '
		f'1. title: The article headline '
		f'2. url: The full URL of the article page '
		f'3. posting_time: The publication date/time as shown on the page '
		f"4. short_summary: A 10-word overview of the article's content "
		f'5. long_summary: A 100-word detailed summary of the article '
		f"6. sentiment: Classify as 'positive', 'neutral', or 'negative' based on the article tone. "
		f'When done, call the done action with success=True and put ALL extracted data in the text field '
		f'as valid JSON in this exact format: '
		f'{{"title": "...", "url": "...", "posting_time": "...", "short_summary": "...", "long_summary": "...", "sentiment": "positive|neutral|negative"}}'
	)

	llm = ChatGoogle(model='gemini-2.0-flash', temperature=0.1, api_key=GEMINI_API_KEY)
	browser_session = BrowserSession(headless=not debug)

	agent = Agent(task=prompt, llm=llm, browser_session=browser_session, use_vision=False)

	if debug:
		print(f'[DEBUG] Starting extraction from {site_url}')
		start = time.time()

	result = await agent.run(max_steps=25)

	raw = result.final_result() if result else None
	if debug:
		print(f'[DEBUG] Raw result type: {type(raw)}')
		print(f'[DEBUG] Raw result: {raw[:500] if isinstance(raw, str) else raw}')
		print(f'[DEBUG] Extraction time: {time.time() - start:.2f}s')

	if isinstance(raw, dict):
		return {'status': 'success', 'data': raw}

	text = str(raw).strip() if raw else ''

	if '<json>' in text and '</json>' in text:
		text = text.split('<json>', 1)[1].split('</json>', 1)[0].strip()

	if text.lower().startswith('here is'):
		brace = text.find('{')
		if brace != -1:
			text = text[brace:]

	if text.startswith('```'):
		text = text.lstrip('`\n ')
		if text.lower().startswith('json'):
			text = text[4:].lstrip()

	def _escape_newlines(src: str) -> str:
		out, in_str, esc = [], False, False
		for ch in src:
			if in_str:
				if esc:
					esc = False
				elif ch == '\\':
					esc = True
				elif ch == '"':
					in_str = False
				elif ch == '\n':
					out.append('\\n')
					continue
				elif ch == '\r':
					continue
			else:
				if ch == '"':
					in_str = True
			out.append(ch)
		return ''.join(out)

	cleaned = _escape_newlines(text)

	def _try_parse(txt: str):
		try:
			return json.loads(txt)
		except Exception:
			return None

	data = _try_parse(cleaned)

	# Fallback: grab first balanced JSON object
	if data is None:
		brace = 0
		start = None
		for i, ch in enumerate(text):
			if ch == '{':
				if brace == 0:
					start = i
				brace += 1
			elif ch == '}':
				brace -= 1
				if brace == 0 and start is not None:
					candidate = _escape_newlines(text[start : i + 1])
					data = _try_parse(candidate)
					if data is not None:
						break

	if isinstance(data, dict):
		return {'status': 'success', 'data': data}
	return {'status': 'error', 'error': f'JSON parse failed. Raw head: {text[:200]}'}
async def monitor(url: str, interval: int, output_path: str, debug: bool):
	"""Continuous monitoring mode"""
	seen = load_seen_hashes(output_path)
	print(f'Monitoring {url} every {interval}s')
	print()

	while True:
		try:
			res = await extract_latest_article(url, debug)

			if res['status'] == 'success':
				art = res['data']
				url_val = art.get('url', '')
				hash_ = hashlib.md5(url_val.encode()).hexdigest() if url_val else None
				if hash_ and hash_ not in seen:
					seen.add(hash_)
					ts = _fmt(art.get('posting_time', ''))
					sentiment = art.get('sentiment', 'neutral')
					emoji = {'positive': '🟢', 'negative': '🔴', 'neutral': '🟡'}.get(sentiment, '🟡')
					summary = art.get('short_summary', art.get('title', ''))
					save_article(art, output_path)
					if debug:
						print(json.dumps(art, ensure_ascii=False, indent=2))
					print(f'[{ts}] - {emoji} - {summary}')
					if not debug:
						print()  # Add spacing between articles in non-debug mode
			elif debug:
				print(f'Error: {res["error"]}')

		except Exception as e:
			if debug:
				import traceback

				traceback.print_exc()
			else:
				print(f'Unhandled error: {e}')

		await asyncio.sleep(interval)
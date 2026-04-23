async def create_multiple_ads(url: str, debug: bool = False, mode: str = 'instagram', count: int = 1):
	"""Generate multiple ads in parallel using asyncio concurrency"""
	if count == 1:
		return await create_ad_from_landing_page(url, debug, mode, 1)

	print(f'🚀 Analyzing {url} for {count} {mode} ads...')

	analyzer = LandingPageAnalyzer(debug=debug)
	page_data = await analyzer.analyze_landing_page(url, mode=mode)

	print(f'🎯 Generating {count} {mode} ads in parallel...')

	tasks = []
	for i in range(count):
		task = create_task_with_error_handling(generate_single_ad(page_data, mode, i + 1), name=f'generate_ad_{i + 1}')
		tasks.append(task)

	results = await asyncio.gather(*tasks, return_exceptions=True)

	successful = []
	failed = []

	for i, result in enumerate(results):
		if isinstance(result, Exception):
			failed.append(i + 1)
		else:
			successful.append(result)

	print(f'\n✅ Successfully generated {len(successful)}/{count} ads')
	if failed:
		print(f'❌ Failed ads: {failed}')

	if page_data.get('screenshot_path'):
		print(f'📸 Page screenshot: {page_data["screenshot_path"]}')

	for ad_path in successful:
		open_file(ad_path)

	return successful
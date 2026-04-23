async def create_ad_from_landing_page(url: str, debug: bool = False, mode: str = 'instagram', ad_id: int = 1):
	analyzer = LandingPageAnalyzer(debug=debug)

	try:
		if ad_id == 1:
			print(f'🚀 Analyzing {url} for {mode.capitalize()} ad...')
			page_data = await analyzer.analyze_landing_page(url, mode=mode)
		else:
			analyzer_temp = LandingPageAnalyzer(debug=debug)
			page_data = await analyzer_temp.analyze_landing_page(url, mode=mode)

		generator = AdGenerator(mode=mode)

		if mode == 'instagram':
			prompt = generator.create_ad_prompt(page_data['analysis'])
			ad_content = await generator.generate_ad_image(prompt, page_data.get('screenshot_path'))
			if ad_content is None:
				raise RuntimeError(f'Ad image generation failed for ad #{ad_id}')
		else:  # tiktok
			video_concept = await generator.create_video_concept(page_data['analysis'], ad_id)
			prompt = generator.create_ad_prompt(page_data['analysis'], video_concept)
			ad_content = await generator.generate_ad_video(prompt, page_data.get('screenshot_path'), ad_id)

		result_path = await generator.save_results(ad_content, prompt, page_data['analysis'], url, page_data['timestamp'])

		if mode == 'instagram':
			print(f'🎨 Generated image ad #{ad_id}: {result_path}')
		else:
			print(f'🎬 Generated video ad #{ad_id}: {result_path}')

		open_file(result_path)

		return result_path

	except Exception as e:
		print(f'❌ Error for ad #{ad_id}: {e}')
		raise
	finally:
		if ad_id == 1 and page_data.get('screenshot_path'):
			print(f'📸 Page screenshot: {page_data["screenshot_path"]}')
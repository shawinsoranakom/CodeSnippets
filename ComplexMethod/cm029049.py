async def main():
	"""Demonstrate comprehensive Search API usage."""
	print('🔍 Browser Use Cloud - Search API (BETA)')
	print('=' * 45)

	print('⚠️  Note: This API is in BETA and may change')
	print()
	print('🎯 Search API Features:')
	print('• Real-time website browsing (not cached)')
	print('• Deep navigation through multiple pages')
	print('• Dynamic content and JavaScript handling')
	print('• Multiple result aggregation')
	print('• Cost-effective content extraction')

	print('\n💰 Pricing:')
	print('• Simple Search: 1¢ × depth × websites')
	print('• URL Search: 1¢ × depth')
	print('• Example: depth=2, 5 websites = 10¢')

	try:
		# Parse command line arguments
		parser = argparse.ArgumentParser(description='Search API (BETA) examples')
		parser.add_argument(
			'--demo',
			choices=['news', 'competitive', 'deep', 'product', 'realtime', 'depth', 'all'],
			default='news',
			help='Which demo to run',
		)
		args = parser.parse_args()

		print(f'\n🔍 Running {args.demo} demo(s)...')

		if args.demo == 'news':
			await demo_news_search()
		elif args.demo == 'competitive':
			await demo_competitive_analysis()
		elif args.demo == 'deep':
			await demo_deep_website_analysis()
		elif args.demo == 'product':
			await demo_product_research()
		elif args.demo == 'realtime':
			await demo_real_time_vs_cached()
		elif args.demo == 'depth':
			await demo_search_depth_comparison()
		elif args.demo == 'all':
			await demo_news_search()
			await demo_competitive_analysis()
			await demo_deep_website_analysis()
			await demo_product_research()
			await demo_real_time_vs_cached()
			await demo_search_depth_comparison()

	except aiohttp.ClientError as e:
		print(f'❌ Network Error: {e}')
	except Exception as e:
		print(f'❌ Error: {e}')
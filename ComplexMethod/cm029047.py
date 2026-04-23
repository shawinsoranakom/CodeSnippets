def main():
	"""Demonstrate comprehensive proxy usage."""
	print('🌍 Browser Use Cloud - Proxy Usage Examples')
	print('=' * 50)

	print('🎯 Proxy Benefits:')
	print('• Bypass geo-restrictions')
	print('• Test location-specific content')
	print('• Access region-locked websites')
	print('• Mobile/residential IP addresses')
	print('• Verify IP geolocation')

	print('\n🌐 Available Countries:')
	countries = ['🇺🇸 US', '🇫🇷 France', '🇮🇹 Italy', '🇯🇵 Japan', '🇦🇺 Australia', '🇩🇪 Germany', '🇫🇮 Finland', '🇨🇦 Canada']
	print(' • '.join(countries))

	try:
		# Parse command line arguments
		parser = argparse.ArgumentParser(description='Proxy usage examples')
		parser.add_argument(
			'--demo', choices=['countries', 'geo', 'streaming', 'search', 'all'], default='countries', help='Which demo to run'
		)
		args = parser.parse_args()

		print(f'\n🔍 Running {args.demo} demo(s)...')

		if args.demo == 'countries':
			demo_proxy_countries()
		elif args.demo == 'geo':
			demo_geo_restrictions()
		elif args.demo == 'streaming':
			demo_streaming_access()
		elif args.demo == 'search':
			demo_search_localization()
		elif args.demo == 'all':
			demo_proxy_countries()
			demo_geo_restrictions()
			demo_streaming_access()
			demo_search_localization()

	except requests.exceptions.RequestException as e:
		print(f'❌ API Error: {e}')
	except Exception as e:
		print(f'❌ Error: {e}')
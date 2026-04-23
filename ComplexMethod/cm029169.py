def _download_and_convert_image(url: str) -> tuple[str, bytes]:
		"""Download an image from URL and convert to base64 bytes."""
		try:
			import httpx
		except ImportError:
			raise ImportError('httpx not available. Please install it to use URL images with AWS Bedrock.')

		try:
			response = httpx.get(url, timeout=30)
			response.raise_for_status()

			# Detect format from content type or URL
			content_type = response.headers.get('content-type', '').lower()
			if 'jpeg' in content_type or url.lower().endswith(('.jpg', '.jpeg')):
				image_format = 'jpeg'
			elif 'png' in content_type or url.lower().endswith('.png'):
				image_format = 'png'
			elif 'gif' in content_type or url.lower().endswith('.gif'):
				image_format = 'gif'
			elif 'webp' in content_type or url.lower().endswith('.webp'):
				image_format = 'webp'
			else:
				image_format = 'jpeg'  # Default format

			return image_format, response.content

		except Exception as e:
			raise ValueError(f'Failed to download image from {url}: {e}')
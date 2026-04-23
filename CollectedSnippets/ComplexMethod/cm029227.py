def _extract_start_url(self, task: str) -> str | None:
		"""Extract URL from task string using naive pattern matching."""

		import re

		# Remove email addresses from task before looking for URLs
		task_without_emails = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '', task)

		# Look for common URL patterns
		patterns = [
			r'https?://[^\s<>"\']+',  # Full URLs with http/https
			r'(?:www\.)?[a-zA-Z0-9-]+(?:\.[a-zA-Z0-9-]+)*\.[a-zA-Z]{2,}(?:/[^\s<>"\']*)?',  # Domain names with subdomains and optional paths
		]

		# File extensions that should be excluded from URL detection
		# These are likely files rather than web pages to navigate to
		excluded_extensions = {
			# Documents
			'pdf',
			'doc',
			'docx',
			'xls',
			'xlsx',
			'ppt',
			'pptx',
			'odt',
			'ods',
			'odp',
			# Text files
			'txt',
			'md',
			'csv',
			'json',
			'xml',
			'yaml',
			'yml',
			# Archives
			'zip',
			'rar',
			'7z',
			'tar',
			'gz',
			'bz2',
			'xz',
			# Images
			'jpg',
			'jpeg',
			'png',
			'gif',
			'bmp',
			'svg',
			'webp',
			'ico',
			# Audio/Video
			'mp3',
			'mp4',
			'avi',
			'mkv',
			'mov',
			'wav',
			'flac',
			'ogg',
			# Code/Data
			'py',
			'js',
			'css',
			'java',
			'cpp',
			# Academic/Research
			'bib',
			'bibtex',
			'tex',
			'latex',
			'cls',
			'sty',
			# Other common file types
			'exe',
			'msi',
			'dmg',
			'pkg',
			'deb',
			'rpm',
			'iso',
			# GitHub/Project paths
			'polynomial',
		}

		excluded_words = {
			'never',
			'dont',
			'not',
			"don't",
		}

		found_urls = []
		for pattern in patterns:
			matches = re.finditer(pattern, task_without_emails)
			for match in matches:
				url = match.group(0)
				original_position = match.start()  # Store original position before URL modification

				# Remove trailing punctuation that's not part of URLs
				url = re.sub(r'[.,;:!?()\[\]]+$', '', url)

				# Check if URL ends with a file extension that should be excluded
				url_lower = url.lower()
				should_exclude = False
				for ext in excluded_extensions:
					if f'.{ext}' in url_lower:
						should_exclude = True
						break

				if should_exclude:
					self.logger.debug(f'Excluding URL with file extension from auto-navigation: {url}')
					continue

				# If in the 20 characters before the url position is a word in excluded_words skip to avoid "Never go to this url"
				context_start = max(0, original_position - 20)
				context_text = task_without_emails[context_start:original_position]
				if any(word.lower() in context_text.lower() for word in excluded_words):
					self.logger.debug(
						f'Excluding URL with word in excluded words from auto-navigation: {url} (context: "{context_text.strip()}")'
					)
					continue

				# Add https:// if missing (after excluded words check to avoid position calculation issues)
				if not url.startswith(('http://', 'https://')):
					url = 'https://' + url

				found_urls.append(url)

		unique_urls = list(set(found_urls))
		# If multiple URLs found, skip directly_open_urling
		if len(unique_urls) > 1:
			self.logger.debug(f'Multiple URLs found ({len(found_urls)}), skipping directly_open_url to avoid ambiguity')
			return None

		# If exactly one URL found, return it
		if len(unique_urls) == 1:
			return unique_urls[0]

		return None
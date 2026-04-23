def format(self, record):
			# Only clean up names in INFO mode, keep everything in DEBUG mode
			if self.log_level > logging.DEBUG and isinstance(record.name, str) and record.name.startswith('browser_use.'):
				# Extract clean component names from logger names
				if 'Agent' in record.name:
					record.name = 'Agent'
				elif 'BrowserSession' in record.name:
					record.name = 'BrowserSession'
				elif 'tools' in record.name:
					record.name = 'tools'
				elif 'dom' in record.name:
					record.name = 'dom'
				elif record.name.startswith('browser_use.'):
					# For other browser_use modules, use the last part
					parts = record.name.split('.')
					if len(parts) >= 2:
						record.name = parts[-1]
			return super().format(record)
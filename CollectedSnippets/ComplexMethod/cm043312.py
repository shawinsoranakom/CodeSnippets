def _is_nonsense_url(self, url: str) -> bool:
        """
        Check if URL is a utility/nonsense URL that shouldn't be crawled.
        Returns True if the URL should be filtered out.
        """
        url_lower = url.lower()

        # Extract path and filename
        from urllib.parse import urlparse
        parsed = urlparse(url)
        path = parsed.path.lower()

        # 1. Robot and sitemap files
        if path.endswith(('/robots.txt', '/sitemap.xml', '/sitemap_index.xml')):
            return True

        # 2. Sitemap variations
        if '/sitemap' in path and path.endswith(('.xml', '.xml.gz', '.txt')):
            return True

        # 3. Common utility files
        utility_files = [
            'ads.txt', 'humans.txt', 'security.txt', '.well-known/security.txt',
            'crossdomain.xml', 'browserconfig.xml', 'manifest.json',
            'apple-app-site-association', '.well-known/apple-app-site-association',
            'favicon.ico', 'apple-touch-icon.png', 'android-chrome-192x192.png'
        ]
        if any(path.endswith(f'/{file}') for file in utility_files):
            return True

        # # 4. Feed files
        # if path.endswith(('.rss', '.atom', '/feed', '/rss', '/atom', '/feed.xml', '/rss.xml')):
        #     return True

        # # 5. API endpoints and data files
        # api_patterns = ['/api/', '/v1/', '/v2/', '/v3/', '/graphql', '/.json', '/.xml']
        # if any(pattern in path for pattern in api_patterns):
        #     return True

        # # 6. Archive and download files
        # download_extensions = [
        #     '.zip', '.tar', '.gz', '.rar', '.7z', '.bz2',
        #     '.exe', '.dmg', '.pkg', '.deb', '.rpm',
        #     '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx',
        #     '.csv', '.tsv', '.sql', '.db', '.sqlite'
        # ]
        # if any(path.endswith(ext) for ext in download_extensions):
        #     return True

        # # 7. Media files (often not useful for text content)
        # media_extensions = [
        #     '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg', '.webp', '.ico',
        #     '.mp4', '.avi', '.mov', '.wmv', '.flv', '.webm',
        #     '.mp3', '.wav', '.ogg', '.m4a', '.flac',
        #     '.woff', '.woff2', '.ttf', '.eot', '.otf'
        # ]
        # if any(path.endswith(ext) for ext in media_extensions):
        #     return True

        # # 8. Source code and config files
        # code_extensions = [
        #     '.js', '.css', '.scss', '.sass', '.less',
        #     '.map', '.min.js', '.min.css',
        #     '.py', '.rb', '.php', '.java', '.cpp', '.h',
        #     '.yaml', '.yml', '.toml', '.ini', '.conf', '.config'
        # ]
        # if any(path.endswith(ext) for ext in code_extensions):
        #     return True

        # 9. Hidden files and directories
        path_parts = path.split('/')
        if any(part.startswith('.') for part in path_parts if part):
            return True

        # 10. Common non-content paths
        non_content_paths = [
            '/wp-admin', '/wp-includes', '/wp-content/uploads',
            '/admin', '/login', '/signin', '/signup', '/register',
            '/checkout', '/cart', '/account', '/profile',
            '/search', '/404', '/error',
            '/.git', '/.svn', '/.hg',
            '/cgi-bin', '/scripts', '/includes'
        ]
        if any(ncp in path for ncp in non_content_paths):
            return True

        # 11. URL patterns that indicate non-content
        if any(pattern in url_lower for pattern in ['?print=', '&print=', '/print/', '_print.']):
            return True

        # 12. Very short paths (likely homepage redirects or errors)
        if len(path.strip('/')) < 3 and path not in ['/', '/en', '/de', '/fr', '/es', '/it']:
            return True

        return False
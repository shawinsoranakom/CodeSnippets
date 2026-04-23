def _extract_filename(self, content_disposition: str, url: str, content_type: str) -> str:
        """Extract filename from Content-Disposition header or URL path."""
        # Try Content-Disposition first
        if content_disposition:
            import re
            # filename*=UTF-8''encoded_name (RFC 5987)
            match = re.search(r"filename\*=(?:UTF-8''|utf-8'')(.+?)(?:;|$)", content_disposition)
            if match:
                from urllib.parse import unquote
                return unquote(match.group(1).strip())
            # filename="name" or filename=name
            match = re.search(r'filename="?([^";]+)"?', content_disposition)
            if match:
                return match.group(1).strip()

        # Fall back to URL path
        path = urlparse(url).path
        if path and '/' in path:
            basename = path.rsplit('/', 1)[-1]
            if '.' in basename and len(basename) <= 255:
                return basename

        # Last resort: hash-based name with extension from content type
        ext_map = {
            'text/csv': '.csv', 'application/pdf': '.pdf',
            'application/zip': '.zip', 'image/png': '.png',
            'image/jpeg': '.jpg', 'application/json': '.json',
            'text/plain': '.txt', 'application/xml': '.xml',
        }
        ext = ext_map.get(content_type, '')
        return f"download_{hashlib.md5(url.encode()).hexdigest()[:10]}{ext}"
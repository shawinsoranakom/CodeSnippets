def _extract_original_format(self, url, video_id, unlisted_hash=None):
        query = {'action': 'load_download_config'}
        if unlisted_hash:
            query['unlisted_hash'] = unlisted_hash
        download_data = self._download_json(
            url, video_id, fatal=False, query=query,
            headers={'X-Requested-With': 'XMLHttpRequest'})
        if download_data:
            source_file = download_data.get('source_file')
            if isinstance(source_file, dict):
                download_url = source_file.get('download_url')
                if download_url and not source_file.get('is_cold') and not source_file.get('is_defrosting'):
                    source_name = source_file.get('public_name', 'Original')
                    if self._is_valid_url(download_url, video_id, '%s video' % source_name):
                        ext = (try_get(
                            source_file, lambda x: x['extension'],
                            compat_str) or determine_ext(
                            download_url, None) or 'mp4').lower()
                        return {
                            'url': download_url,
                            'ext': ext,
                            'width': int_or_none(source_file.get('width')),
                            'height': int_or_none(source_file.get('height')),
                            'filesize': parse_filesize(source_file.get('size')),
                            'format_id': source_name,
                            'preference': 1,
                        }
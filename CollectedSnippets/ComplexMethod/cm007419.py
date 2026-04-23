def _call_cms(self, path, video_id, note):
        if not self._CMS_SIGNING:
            index = self._call_api('index', video_id, 'CMS Signing')
            self._CMS_SIGNING = index.get('cms_signing') or {}
            if not self._CMS_SIGNING:
                for signing_policy in index.get('signing_policies', []):
                    signing_path = signing_policy.get('path')
                    if signing_path and signing_path.startswith('/cms/'):
                        name, value = signing_policy.get('name'), signing_policy.get('value')
                        if name and value:
                            self._CMS_SIGNING[name] = value
        return self._download_json(
            self._API_DOMAIN + path, video_id, query=self._CMS_SIGNING,
            note='Downloading %s JSON metadata' % note, headers=self.geo_verification_headers())
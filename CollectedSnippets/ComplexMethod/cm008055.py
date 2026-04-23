def _get_version_info(self, tag: str) -> tuple[str | None, str | None]:
        if _VERSION_RE.fullmatch(tag):
            return tag, None

        api_info = self._call_api(tag)

        if tag == 'latest':
            requested_version = api_info['tag_name']
        else:
            match = re.search(rf'\s+(?P<version>{_VERSION_RE.pattern})$', api_info.get('name', ''))
            requested_version = match.group('version') if match else None

        if re.fullmatch(_HASH_PATTERN, api_info.get('target_commitish', '')):
            target_commitish = api_info['target_commitish']
        else:
            match = _COMMIT_RE.match(api_info.get('body', ''))
            target_commitish = match.group('hash') if match else None

        if not (requested_version or target_commitish):
            self._report_error('One of either version or commit hash must be available on the release', expected=True)

        return requested_version, target_commitish
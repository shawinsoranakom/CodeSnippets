def _get_capture_dates(self, video_id, url_date):
        capture_dates = []
        # Note: CDX API will not find watch pages with extra params in the url.
        response = self._call_cdx_api(
            video_id, f'https://www.youtube.com/watch?v={video_id}',
            filters=['mimetype:text/html'], collapse=['timestamp:6', 'digest'], query={'matchType': 'prefix'}) or []
        all_captures = sorted(int_or_none(r['timestamp']) for r in response if int_or_none(r['timestamp']) is not None)

        # Prefer the new polymer UI captures as we support extracting more metadata from them
        # WBM captures seem to all switch to this layout ~July 2020
        modern_captures = [x for x in all_captures if x >= 20200701000000]
        if modern_captures:
            capture_dates.append(modern_captures[0])
        capture_dates.append(url_date)
        if all_captures:
            capture_dates.append(all_captures[0])

        if 'captures' in self._configuration_arg('check_all'):
            capture_dates.extend(modern_captures + all_captures)

        # Fallbacks if any of the above fail
        capture_dates.extend([self._OLDEST_CAPTURE_DATE, self._NEWEST_CAPTURE_DATE])
        return orderedSet(filter(None, capture_dates))
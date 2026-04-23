def _real_extract(self, url):
        base_url, show_id = re.match(self._VALID_URL, url).groups()

        result = self._call_api(
            'teaserrow/format/navigation/' + show_id, show_id)

        items = result['items']

        entries = []
        navigation = result.get('navigationType')
        if navigation == 'annual':
            for item in items:
                if not isinstance(item, dict):
                    continue
                year = int_or_none(item.get('year'))
                if year is None:
                    continue
                months = item.get('months')
                if not isinstance(months, list):
                    continue
                for month_dict in months:
                    if not isinstance(month_dict, dict) or not month_dict:
                        continue
                    month_number = int_or_none(list(month_dict.keys())[0])
                    if month_number is None:
                        continue
                    entries.append(self.url_result(
                        '%s/%04d-%02d' % (base_url, year, month_number),
                        ie=TVNowAnnualIE.ie_key()))
        elif navigation == 'season':
            for item in items:
                if not isinstance(item, dict):
                    continue
                season_number = int_or_none(item.get('season'))
                if season_number is None:
                    continue
                entries.append(self.url_result(
                    '%s/staffel-%d' % (base_url, season_number),
                    ie=TVNowSeasonIE.ie_key()))
        else:
            raise ExtractorError('Unknown navigationType')

        return self.playlist_result(entries, show_id)
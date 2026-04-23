def _check_errors(self, data):
        for reason, status in (data.get('blocking') or {}).items():
            if status and reason in self._ERRORS:
                message = self._ERRORS[reason]
                if reason == 'geo':
                    self.raise_geo_restricted(msg=message)
                elif reason == 'paywall':
                    if try_get(data, lambda x: x['paywallable']['tvod']):
                        self._raise_error('This video is for rent only or TVOD (Transactional Video On demand)')
                    self.raise_login_required(message)
                self._raise_error(message)
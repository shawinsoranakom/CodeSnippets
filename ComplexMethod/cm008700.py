def _extract_data(self, url, item_id, ytcfg=None, fatal=True, webpage_fatal=False, default_client='web'):
        data = None
        if not self.skip_webpage:
            webpage, data = self._extract_webpage(url, item_id, fatal=webpage_fatal)
            ytcfg = ytcfg or self.extract_ytcfg(item_id, webpage)
            # Reject webpage data if redirected to home page without explicitly requesting
            selected_tab = self._extract_selected_tab(self._extract_tab_renderers(data), fatal=False) or {}
            if (url != 'https://www.youtube.com/feed/recommended'
                    and selected_tab.get('tabIdentifier') == 'FEwhat_to_watch'  # Home page
                    and 'no-youtube-channel-redirect' not in self.get_param('compat_opts', [])):
                msg = 'The channel/playlist does not exist and the URL redirected to youtube.com home page'
                if fatal:
                    raise ExtractorError(msg, expected=True)
                self.report_warning(msg, only_once=True)
        if not data:
            self._report_playlist_authcheck(ytcfg, fatal=fatal)
            data = self._extract_tab_endpoint(url, item_id, ytcfg, fatal=fatal, default_client=default_client)
        return data, ytcfg
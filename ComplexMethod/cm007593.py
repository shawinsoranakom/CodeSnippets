def __check_blocked(self, content):
        first_block = content[:512]
        if ('<title>Access to this site is blocked</title>' in content
                and 'Websense' in first_block):
            msg = 'Access to this webpage has been blocked by Websense filtering software in your network.'
            blocked_iframe = self._html_search_regex(
                r'<iframe src="([^"]+)"', content,
                'Websense information URL', default=None)
            if blocked_iframe:
                msg += ' Visit %s for more details' % blocked_iframe
            raise ExtractorError(msg, expected=True)
        if '<title>The URL you requested has been blocked</title>' in first_block:
            msg = (
                'Access to this webpage has been blocked by Indian censorship. '
                'Use a VPN or proxy server (with --proxy) to route around it.')
            block_msg = self._html_search_regex(
                r'</h1><p>(.*?)</p>',
                content, 'block message', default=None)
            if block_msg:
                msg += ' (Message: "%s")' % block_msg.replace('\n', ' ')
            raise ExtractorError(msg, expected=True)
        if ('<title>TTK :: Доступ к ресурсу ограничен</title>' in content
                and 'blocklist.rkn.gov.ru' in content):
            raise ExtractorError(
                'Access to this webpage has been blocked by decision of the Russian government. '
                'Visit http://blocklist.rkn.gov.ru/ for a block reason.',
                expected=True)
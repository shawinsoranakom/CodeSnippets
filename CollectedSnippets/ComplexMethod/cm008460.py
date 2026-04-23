def _solve_challenge_and_set_cookies(self, webpage):
        challenge_data = traverse_obj(webpage, (
            {find_element(id='cs', html=True)}, {extract_attributes}, 'class',
            filter, {lambda x: f'{x}==='}, {base64.b64decode}, {json.loads}))

        if not challenge_data:
            if 'Please wait...' in webpage:
                raise ExtractorError('Unable to extract challenge data')
            raise ExtractorError('Unexpected response from webpage request')

        self.to_screen('Solving JS challenge using native Python implementation')

        expected_digest = traverse_obj(challenge_data, (
            'v', 'c', {str}, {base64.b64decode},
            {require('challenge expected digest')}))

        base_hash = traverse_obj(challenge_data, (
            'v', 'a', {str}, {base64.b64decode},
            {hashlib.sha256}, {require('challenge base hash')}))

        for i in range(1_000_001):
            number = str(i).encode()
            test_hash = base_hash.copy()
            test_hash.update(number)
            if test_hash.digest() == expected_digest:
                challenge_data['d'] = base64.b64encode(number).decode()
                break
        else:
            raise ExtractorError('Unable to solve JS challenge')

        wci_cookie_value = base64.b64encode(
            json.dumps(challenge_data, separators=(',', ':')).encode()).decode()

        # At time of writing, the wci cookie name was `_wafchallengeid`
        wci_cookie_name = traverse_obj(webpage, (
            {find_element(id='wci', html=True)}, {extract_attributes},
            'class', {require('challenge cookie name')}))

        # At time of writing, the **optional** rci cookie name was `waforiginalreid`
        rci_cookie_name = traverse_obj(webpage, (
            {find_element(id='rci', html=True)}, {extract_attributes}, 'class'))
        rci_cookie_value = traverse_obj(webpage, (
            {find_element(id='rs', html=True)}, {extract_attributes}, 'class'))

        # Actual JS sets Max-Age=1 for the cookies, but we'll manually clear them later instead
        expire_time = int(time.time()) + (self.get_param('sleep_interval_requests') or 0) + 120
        self._set_cookie('.tiktok.com', wci_cookie_name, wci_cookie_value, expire_time=expire_time)
        if rci_cookie_name and rci_cookie_value:
            self._set_cookie('.tiktok.com', rci_cookie_name, rci_cookie_value, expire_time=expire_time)

        return wci_cookie_name, rci_cookie_name
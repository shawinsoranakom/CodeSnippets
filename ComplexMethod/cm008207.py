def fetch_page(page_idx):
            query = {
                'keyword': '',
                'mid': playlist_id,
                'order': traverse_obj(parse_qs(url), ('order', 0)) or 'pubdate',
                'order_avoided': 'true',
                'platform': 'web',
                'pn': page_idx + 1,
                'ps': 30,
                'tid': 0,
                'web_location': 1550101,
                'dm_img_list': '[]',
                'dm_img_str': base64.b64encode(
                    ''.join(random.choices(string.printable, k=random.randint(16, 64))).encode())[:-2].decode(),
                'dm_cover_img_str': base64.b64encode(
                    ''.join(random.choices(string.printable, k=random.randint(32, 128))).encode())[:-2].decode(),
                'dm_img_inter': '{"ds":[],"wh":[6093,6631,31],"of":[430,760,380]}',
            }

            try:
                response = self._download_json(
                    'https://api.bilibili.com/x/space/wbi/arc/search', playlist_id,
                    query=self._sign_wbi(query, playlist_id),
                    note=f'Downloading space page {page_idx}', headers={'Referer': url})
            except ExtractorError as e:
                if isinstance(e.cause, HTTPError) and e.cause.status == 412:
                    raise ExtractorError(
                        'Request is blocked by server (412), please wait and try later.', expected=True)
                raise
            status_code = response['code']
            if status_code == -401:
                raise ExtractorError(
                    'Request is blocked by server (401), please wait and try later.', expected=True)
            elif status_code == -352:
                raise ExtractorError('Request is rejected by server (352)', expected=True)
            elif status_code != 0:
                raise ExtractorError(f'Request failed ({status_code}): {response.get("message") or "Unknown error"}')
            return response['data']
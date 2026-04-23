def create_completion(
        cls,
        model: str,
        messages: Messages,
        stream: bool = True,
        proxy: str = None,
        api_key: str = None,
        image: ImageType = None,
        **kwargs
    ) -> CreateResult:
        cls.proxy = proxy

        if not api_key:
            cls.cookies = get_cookies(cls.domain,cache_result=False)
            if not cls.cookies:
                raise ValueError(f"No cookies found for {cls.domain}")
            elif "appSession" not in cls.cookies:
                raise ValueError(f"No appSession found in cookies for {cls.domain}, log in or provide bearer_auth")
            api_key = cls.get_access_token(cls)

        conversation = []
        for message in messages:
            conversation.append({
                "type": "human",
                "text": message["content"],
            })

        if image:
            image_url = cls.upload_image(cls, api_key, image)
            conversation[-1]["image_url"] = image_url
            conversation[-1]["media_type"] = "image"

        headers = {
            'accept': '*/*',
            'accept-language': 'en,fr-FR;q=0.9,fr;q=0.8,es-ES;q=0.7,es;q=0.6,en-US;q=0.5,am;q=0.4,de;q=0.3',
            'authorization': f'Bearer {api_key}',
            'cache-control': 'no-cache',
            'content-type': 'application/json',
            'origin': cls.url,
            'pragma': 'no-cache',
            'priority': 'u=1, i',
            'sec-ch-ua': '"Chromium";v="124", "Google Chrome";v="124", "Not-A.Brand";v="99"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"macOS"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-origin',
            'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
        }

        json_data = {
            'conversation_history': conversation,
            'stream': True,
            'use_search_engine': False,
            'use_code_interpreter': False,
            'model_name': 'reka-core',
            'random_seed': int(time.time() * 1000),
        }

        tokens = ''

        response = requests.post(f'{cls.url}/api/chat', 
                                cookies=cls.cookies, headers=headers, json=json_data, proxies=cls.proxy, stream=True)

        for completion in response.iter_lines():
            if b'data' in completion:
                token_data = json.loads(completion.decode('utf-8')[5:])['text']

                yield (token_data.replace(tokens, ''))

                tokens = token_data
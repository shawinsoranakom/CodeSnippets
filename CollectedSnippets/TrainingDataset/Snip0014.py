 def setUp(self):
        self.duplicate_links = [
            'https://www.example.com',
            'https://www.example.com',
            'https://www.example.com',
            'https://www.anotherexample.com',
        ]
        self.no_duplicate_links = [
            'https://www.firstexample.com',
            'https://www.secondexample.com',
            'https://www.anotherexample.com',
        ]

        self.code_200 = 200
        self.code_403 = 403
        self.code_503 = 503

        self.cloudflare_headers = {'Server': 'cloudflare'}
        self.no_cloudflare_headers = {'Server': 'google'}

        self.text_with_cloudflare_flags = '403 Forbidden Cloudflare We are checking your browser...'
        self.text_without_cloudflare_flags = 'Lorem Ipsum'

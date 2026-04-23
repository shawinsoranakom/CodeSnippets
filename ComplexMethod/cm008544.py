def extract_redirect_urls(info):
            for encoding_name in ('recommended_encoding', 'alternate_encoding'):
                redirect = info.get(encoding_name)
                if not redirect:
                    continue
                redirect_url = redirect.get('url')
                if redirect_url and redirect_url not in redirect_urls:
                    redirects.append(redirect)
                    redirect_urls.add(redirect_url)
            encodings = info.get('encodings')
            if isinstance(encodings, list):
                for encoding in encodings:
                    encoding_url = url_or_none(encoding)
                    if encoding_url and encoding_url not in redirect_urls:
                        redirects.append({'url': encoding_url})
                        redirect_urls.add(encoding_url)
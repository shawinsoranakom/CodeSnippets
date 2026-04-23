def _calc_request_body_size(self, e: _HarEntryBuilder) -> int:
		# Try Content-Length header first; else post_data; else request_body; else 0 for GET/HEAD, -1 if unknown
		try:
			cl = None
			if e.request_headers:
				cl = e.request_headers.get('content-length') or e.request_headers.get('Content-Length')
			if cl is not None:
				return int(cl)
			if e.post_data:
				return len(e.post_data.encode('utf-8'))
			if e.request_body is not None:
				return len(e.request_body)
			# GET/HEAD requests typically have no body
			if e.method and e.method.upper() in ('GET', 'HEAD'):
				return 0
		except Exception:
			pass
		return -1
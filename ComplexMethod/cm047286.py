def _compute_mimetype(self, values):
        """ compute the mimetype of the given values
            :param values : dict of values to create or write an ir_attachment
            :return mime : string indicating the mimetype, or application/octet-stream by default
        """
        mimetype = None
        if values.get('mimetype'):
            mimetype = values['mimetype']
        if not mimetype and values.get('name'):
            mimetype = mimetypes.guess_type(values['name'])[0]
        if not mimetype and values.get('url'):
            mimetype = mimetypes.guess_type(values['url'].split('?')[0])[0]
        if not mimetype or mimetype == 'application/octet-stream':
            raw = None
            if values.get('raw'):
                raw = values['raw']
            elif values.get('datas'):
                raw = base64.b64decode(values['datas'])
            if raw:
                mimetype = guess_mimetype(raw)
        return mimetype and mimetype.lower() or 'application/octet-stream'
def _apply_onchange_methods(self, field_name: str, result: dict) -> None:
        """ Apply onchange method(s) for field ``field_name`` on ``self``. Value
            assignments are applied on ``self``, while warning messages are put
            in dictionary ``result``.
        """
        for method in self._onchange_methods.get(field_name, ()):
            res = method(self)
            if not res:
                continue
            if res.get('value'):
                for key, val in res['value'].items():
                    if key in self._fields and key != 'id':
                        self[key] = val
            if res.get('warning'):
                result['warnings'].add((
                    res['warning'].get('title') or _("Warning"),
                    res['warning'].get('message') or "",
                    res['warning'].get('type') or "",
                ))
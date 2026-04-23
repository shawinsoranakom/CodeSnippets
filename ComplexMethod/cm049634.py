def _search_render_results(self, fetch_fields, mapping, icon, limit):
        results_data = self.read(fetch_fields)[:limit]
        for result in results_data:
            result['_fa'] = icon
            result['_mapping'] = mapping
        html_fields = [config['name'] for config in mapping.values() if config.get('html')]
        if html_fields:
            for data in results_data:
                for html_field in html_fields:
                    if data[html_field]:
                        if html_field == 'arch':
                            # Undo second escape of text nodes from wywsiwyg.js _getEscapedElement.
                            data[html_field] = re.sub(r'&amp;(?=\w+;)', '&', data[html_field])
                        text = text_from_html(data[html_field], True)
                        data[html_field] = text
        return results_data
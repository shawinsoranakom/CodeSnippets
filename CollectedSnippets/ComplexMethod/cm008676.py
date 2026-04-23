def _parse_content_as_text(self, content):
        outer_contents, joined_contents = content.get('content') or [], []
        for outer_content in outer_contents:
            if outer_content.get('type') != 'paragraph':
                joined_contents.append(self._parse_content_as_text(outer_content))
                continue
            inner_contents, inner_content_text = outer_content.get('content') or [], ''
            for inner_content in inner_contents:
                if inner_content.get('text'):
                    inner_content_text += inner_content['text']
                elif inner_content.get('type') == 'hardBreak':
                    inner_content_text += '\n'
            joined_contents.append(inner_content_text)

        return '\n'.join(joined_contents)
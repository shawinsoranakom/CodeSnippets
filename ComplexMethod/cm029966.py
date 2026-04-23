def showtopic(self, topic, more_xrefs=''):
        try:
            import pydoc_data.topics
        except ImportError:
            self.output.write('''
Sorry, topic and keyword documentation is not available because the
module "pydoc_data.topics" could not be found.
''')
            return
        target = self.topics.get(topic, self.keywords.get(topic))
        if not target:
            self.output.write('no documentation found for %s\n' % repr(topic))
            return
        if isinstance(target, str):
            return self.showtopic(target, more_xrefs)

        label, xrefs = target
        try:
            doc = pydoc_data.topics.topics[label]
        except KeyError:
            self.output.write('no documentation found for %s\n' % repr(topic))
            return
        doc = doc.strip() + '\n'
        if more_xrefs:
            xrefs = (xrefs or '') + ' ' + more_xrefs
        if xrefs:
            text = 'Related help topics: ' + ', '.join(xrefs.split()) + '\n'
            wrapped_text = textwrap.wrap(text, 72)
            doc += '\n%s\n' % '\n'.join(wrapped_text)

        if self._output is None:
            pager(doc, f'Help on {topic!s}')
        else:
            self.output.write(doc)
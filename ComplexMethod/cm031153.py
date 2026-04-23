def startElementNS(self, name, tagName , attrs):
        # Retrieve xml namespace declaration attributes.
        xmlns_uri = 'http://www.w3.org/2000/xmlns/'
        xmlns_attrs = getattr(self, '_xmlns_attrs', None)
        if xmlns_attrs is not None:
            for aname, value in xmlns_attrs:
                attrs._attrs[(xmlns_uri, aname)] = value
            self._xmlns_attrs = []
        uri, localname = name
        if uri:
            # When using namespaces, the reader may or may not
            # provide us with the original name. If not, create
            # *a* valid tagName from the current context.
            if tagName is None:
                prefix = self._current_context[uri]
                if prefix:
                    tagName = prefix + ":" + localname
                else:
                    tagName = localname
            if self.document:
                node = self.document.createElementNS(uri, tagName)
            else:
                node = self.buildDocument(uri, tagName)
        else:
            # When the tagname is not prefixed, it just appears as
            # localname
            if self.document:
                node = self.document.createElement(localname)
            else:
                node = self.buildDocument(None, localname)

        for aname,value in attrs.items():
            a_uri, a_localname = aname
            if a_uri == xmlns_uri:
                if a_localname == 'xmlns':
                    qname = a_localname
                else:
                    qname = 'xmlns:' + a_localname
                attr = self.document.createAttributeNS(a_uri, qname)
                node.setAttributeNodeNS(attr)
            elif a_uri:
                prefix = self._current_context[a_uri]
                if prefix:
                    qname = prefix + ":" + a_localname
                else:
                    qname = a_localname
                attr = self.document.createAttributeNS(a_uri, qname)
                node.setAttributeNodeNS(attr)
            else:
                attr = self.document.createAttribute(a_localname)
                node.setAttributeNode(attr)
            attr.value = value

        self.lastEvent[1] = [(START_ELEMENT, node), None]
        self.lastEvent = self.lastEvent[1]
        self.push(node)
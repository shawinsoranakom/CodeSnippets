def skim_html(html: str) -> str:
            """Remove non-structural elements using lxml."""
            parser = lxml_html.HTMLParser(remove_comments=True)
            tree = lxml_html.fromstring(html, parser=parser)

            # Remove head section entirely
            for head in tree.xpath('//head'):
                head.getparent().remove(head)

            # Remove non-structural elements including SVGs
            for element in tree.xpath('//script | //style | //noscript | //meta | //link | //svg'):
                parent = element.getparent()
                if parent is not None:
                    parent.remove(element)

            # Remove base64 images
            for img in tree.xpath('//img[@src]'):
                src = img.get('src', '')
                if 'base64' in src:
                    img.set('src', 'BASE64_IMAGE')

            # Remove long class/id attributes
            for element in tree.xpath('//*[@class or @id]'):
                if element.get('class') and len(element.get('class')) > 100:
                    element.set('class', 'LONG_CLASS')
                if element.get('id') and len(element.get('id')) > 50:
                    element.set('id', 'LONG_ID')

            # Truncate text nodes
            for text_node in tree.xpath('//text()'):
                if text_node.strip() and len(text_node) > 100:
                    parent = text_node.getparent()
                    if parent is not None:
                        new_text = text_node[:50] + "..." + text_node[-20:]
                        if text_node.is_text:
                            parent.text = new_text
                        elif text_node.is_tail:
                            parent.tail = new_text

            return lxml_html.tostring(tree, encoding='unicode')
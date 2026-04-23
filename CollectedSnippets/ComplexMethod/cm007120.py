def process_node(self, node):
        blocks = []
        if isinstance(node, str):
            text = node.strip()
            if text:
                if text.startswith("#"):
                    heading_level = text.count("#", 0, 6)
                    heading_text = text[heading_level:].strip()
                    if heading_level in range(3):
                        blocks.append(self.create_block(f"heading_{heading_level + 1}", heading_text))
                else:
                    blocks.append(self.create_block("paragraph", text))
        elif node.name == "h1":
            blocks.append(self.create_block("heading_1", node.get_text(strip=True)))
        elif node.name == "h2":
            blocks.append(self.create_block("heading_2", node.get_text(strip=True)))
        elif node.name == "h3":
            blocks.append(self.create_block("heading_3", node.get_text(strip=True)))
        elif node.name == "p":
            code_node = node.find("code")
            if code_node:
                code_text = code_node.get_text()
                language, code = self.extract_language_and_code(code_text)
                blocks.append(self.create_block("code", code, language=language))
            elif self.is_table(str(node)):
                blocks.extend(self.process_table(node))
            else:
                blocks.append(self.create_block("paragraph", node.get_text(strip=True)))
        elif node.name == "ul":
            blocks.extend(self.process_list(node, "bulleted_list_item"))
        elif node.name == "ol":
            blocks.extend(self.process_list(node, "numbered_list_item"))
        elif node.name == "blockquote":
            blocks.append(self.create_block("quote", node.get_text(strip=True)))
        elif node.name == "hr":
            blocks.append(self.create_block("divider", ""))
        elif node.name == "img":
            blocks.append(self.create_block("image", "", image_url=node.get("src")))
        elif node.name == "a":
            blocks.append(self.create_block("bookmark", node.get_text(strip=True), link_url=node.get("href")))
        elif node.name == "table":
            blocks.extend(self.process_table(node))

        for child in node.children:
            if isinstance(child, str):
                continue
            blocks.extend(self.process_node(child))

        return blocks
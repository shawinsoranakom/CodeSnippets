def characters(self, content):
        if content and re.search(r"[\x00-\x08\x0B-\x0C\x0E-\x1F]", content):
            # Fail loudly when content has control chars (unsupported in XML
            # 1.0) See https://www.w3.org/International/questions/qa-controls
            raise UnserializableContentError(
                "Control characters are not supported in XML 1.0"
            )
        XMLGenerator.characters(self, content)
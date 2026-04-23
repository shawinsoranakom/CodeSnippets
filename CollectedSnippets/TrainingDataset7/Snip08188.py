def item_enclosures(self, item):
        enc_url = self._get_dynamic_attr("item_enclosure_url", item)
        if enc_url:
            enc = feedgenerator.Enclosure(
                url=str(enc_url),
                length=str(self._get_dynamic_attr("item_enclosure_length", item)),
                mime_type=str(self._get_dynamic_attr("item_enclosure_mime_type", item)),
            )
            return [enc]
        return []
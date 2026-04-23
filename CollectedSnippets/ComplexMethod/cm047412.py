def has_text(elem):
            if elem is None:
                return False
            if elem.tag == 'span' and elem.text:
                return True
            if elem.tag in ['field', 'label'] and elem.get('string'):
                return True
            if elem.tag == 't' and (elem.get('t-esc') or elem.get('t-raw')):
                return True
            return False
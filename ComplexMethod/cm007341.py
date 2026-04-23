def load(self, rawdata):
            must_have_value = 0
            if not isinstance(rawdata, dict):
                if sys.version_info[:2] != (2, 7) or sys.platform.startswith('java'):
                    # attribute must have value for parsing
                    rawdata, must_have_value = re.subn(
                        r'(?i)(;\s*)(secure|httponly)(\s*(?:;|$))', r'\1\2=\2\3', rawdata)
                if sys.version_info[0] == 2:
                    if isinstance(rawdata, compat_str):
                        rawdata = str(rawdata)
            super(compat_cookies_SimpleCookie, self).load(rawdata)
            if must_have_value > 0:
                for morsel in self.values():
                    for attr in ('secure', 'httponly'):
                        if morsel.get(attr):
                            morsel[attr] = True
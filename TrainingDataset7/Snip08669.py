def __init__(self, _text, _subtype="plain", _charset=None):
        self.encoding = _charset
        MIMEText.__init__(self, _text, _subtype=_subtype, _charset=_charset)
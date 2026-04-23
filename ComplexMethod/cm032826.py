def _looks_like_header(self, value):
        if len(value) < 1:
            return False
        if any(ord(c) > 127 for c in value):
            return True
        if len([c for c in value if c.isalpha()]) >= 2:
            return True
        if any(c in value for c in ["(", ")", "：", ":", "（", "）", "_", "-"]):
            return True
        return False
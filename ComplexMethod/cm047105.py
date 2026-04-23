def to_splitnum(self, val, hightxt="", lowtxt="", jointxt="",
                    divisor=100, longval=True, cents=True):
        out = []

        if isinstance(val, float):
            high, low = self.float2tuple(val)
        else:
            try:
                high, low = val
            except TypeError:
                high, low = divmod(val, divisor)

        if high:
            hightxt = self.title(self.inflect(high, hightxt))
            out.append(self.to_cardinal(high))
            if low:
                if longval:
                    if hightxt:
                        out.append(hightxt)
                    if jointxt:
                        out.append(self.title(jointxt))
            elif hightxt:
                out.append(hightxt)

        if low:
            if cents:
                out.append(self.to_cardinal(low))
            else:
                out.append("%02d" % low)
            if lowtxt and longval:
                out.append(self.title(self.inflect(low, lowtxt)))

        return " ".join(out)
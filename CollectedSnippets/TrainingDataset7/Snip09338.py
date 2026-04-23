def window_frame_value(self, value):
        if isinstance(value, int):
            if value == 0:
                return self.CURRENT_ROW
            elif value < 0:
                return "%d %s" % (abs(value), self.PRECEDING)
            else:
                return "%d %s" % (value, self.FOLLOWING)
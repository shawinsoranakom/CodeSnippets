def __str__(self):
        if self.start.value is not None and self.start.value < 0:
            start = "%d %s" % (abs(self.start.value), connection.ops.PRECEDING)
        elif self.start.value is not None and self.start.value == 0:
            start = connection.ops.CURRENT_ROW
        elif self.start.value is not None and self.start.value > 0:
            start = "%d %s" % (self.start.value, connection.ops.FOLLOWING)
        else:
            start = connection.ops.UNBOUNDED_PRECEDING

        if self.end.value is not None and self.end.value > 0:
            end = "%d %s" % (self.end.value, connection.ops.FOLLOWING)
        elif self.end.value is not None and self.end.value == 0:
            end = connection.ops.CURRENT_ROW
        elif self.end.value is not None and self.end.value < 0:
            end = "%d %s" % (abs(self.end.value), connection.ops.PRECEDING)
        else:
            end = connection.ops.UNBOUNDED_FOLLOWING
        return self.template % {
            "frame_type": self.frame_type,
            "start": start,
            "end": end,
            "exclude": self.get_exclusion(),
        }
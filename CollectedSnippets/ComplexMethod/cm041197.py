def __eq__(self, other):
        # ignore header in comparison, because timestamp will be different
        if self.service != other.service:
            return False
        if self.operation != other.operation:
            return False
        if self.parameters != other.parameters:
            return False
        if self.response_code != other.response_code:
            return False
        if self.response_data != other.response_data:
            return False
        if self.exception != other.exception:
            return False
        if self.origin != other.origin:
            return False
        if self.xfail != other.xfail:
            return False
        if self.aws_validated != other.aws_validated:
            return False
        if self.node_id != other.node_id:
            return False
        return True
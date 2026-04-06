def __hash__(self):
        return (self.script, self.side_effect).__hash__()
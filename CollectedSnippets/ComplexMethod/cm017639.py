def append(self, element):
        if isinstance(element, str):
            element = normalize_whitespace(element)
            if self.children and isinstance(self.children[-1], str):
                self.children[-1] += element
                self.children[-1] = normalize_whitespace(self.children[-1])
                return
        elif self.children:
            # removing last children if it is only whitespace
            # this can result in incorrect dom representations since
            # whitespace between inline tags like <span> is significant
            if isinstance(self.children[-1], str) and self.children[-1].isspace():
                self.children.pop()
        if element:
            self.children.append(element)
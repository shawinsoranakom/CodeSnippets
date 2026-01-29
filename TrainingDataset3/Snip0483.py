class Node:
    def __init__(self, data=None):
        self.data = data
        self.next = None

    def __repr__(self):
        string_rep = ""
        temp = self
        while temp:
            string_rep += f"<{temp.data}> ---> "
            temp = temp.next
        string_rep += "<END>"
        return string_rep

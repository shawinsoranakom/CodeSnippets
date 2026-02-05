def print_stack(self) -> None:
    print("stack elements are:")
    temp = self.head
    while temp is not None:
        print(temp.data, end="->")
        temp = temp.next

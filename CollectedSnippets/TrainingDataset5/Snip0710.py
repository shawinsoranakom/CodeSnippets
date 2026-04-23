def __len__(self) -> int:
    temp = self.head
    count = 0
    while temp is not None:
        count += 1
        temp = temp.next
    return count

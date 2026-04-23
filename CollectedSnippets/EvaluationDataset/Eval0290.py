class SegmentTree:
    def __init__(self, a):
        self.A = a
        self.N = len(self.A)
        self.st = [0] * (
            4 * self.N
        ) 
        if self.N:
            self.build(1, 0, self.N - 1)

    def left(self, idx):
        return idx * 2

    def right(self, idx):
        return idx * 2 + 1

    def build(self, idx, left, right):
        if left == right:
            self.st[idx] = self.A[left]
        else:
            mid = (left + right) // 2
            self.build(self.left(idx), left, mid)
            self.build(self.right(idx), mid + 1, right)
            self.st[idx] = max(self.st[self.left(idx)], self.st[self.right(idx)])

    def update(self, a, b, val):
        return self.update_recursive(1, 0, self.N - 1, a - 1, b - 1, val)

    def update_recursive(self, idx, left, right, a, b, val):
        if right < a or left > b:
            return True
        if left == right:
            self.st[idx] = val
            return True
        mid = (left + right) // 2
        self.update_recursive(self.left(idx), left, mid, a, b, val)
        self.update_recursive(self.right(idx), mid + 1, right, a, b, val)
        self.st[idx] = max(self.st[self.left(idx)], self.st[self.right(idx)])
        return True

    def query(self, a, b):
        
        return self.query_recursive(1, 0, self.N - 1, a - 1, b - 1)

    def query_recursive(self, idx, left, right, a, b):
        if right < a or left > b:
            return -math.inf
        if left >= a and right <= b:
            return self.st[idx]
        mid = (left + right) // 2
        q1 = self.query_recursive(self.left(idx), left, mid, a, b)
        q2 = self.query_recursive(self.right(idx), mid + 1, right, a, b)
        return max(q1, q2)

    def show_data(self):
        show_list = []
        for i in range(1, self.N + 1):
            show_list += [self.query(i, i)]
        print(show_list)

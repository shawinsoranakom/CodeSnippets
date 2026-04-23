def dfs(self, s=-2, d=-1):
        if s == d:
            return []
        stack = []
        visited = []
        if s == -2:
            s = next(iter(self.graph))
        stack.append(s)
        visited.append(s)
        ss = s

        while True:
            # check if there is any non isolated nodes
            if len(self.graph[s]) != 0:
                ss = s
                for node in self.graph[s]:
                    if visited.count(node[1]) < 1:
                        if node[1] == d:
                            visited.append(d)
                            return visited
                        else:
                            stack.append(node[1])
                            visited.append(node[1])
                            ss = node[1]
                            break

            # check if all the children are visited
            if s == ss:
                stack.pop()
                if len(stack) != 0:
                    s = stack[len(stack) - 1]
            else:
                s = ss

            # check if se have reached the starting point
            if len(stack) == 0:
                return visited
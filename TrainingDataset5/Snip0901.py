def show_path(self, src, dest):
    path = []
    cost = 0
    temp = dest
    while self.par[temp] != -1:
        path.append(temp)
        if temp != src:
            for v, w in self.adjList[temp]:
                if v == self.par[temp]:
                    cost += w
                    break
        temp = self.par[temp]
    path.append(src)
    path.reverse()

    print(f"----Path to reach {dest} from {src}----")
    for u in path:
        print(f"{u}", end=" ")
        if u != dest:
            print("-> ", end="")

    print("\nTotal cost of path: ", cost)


def find_optimal_binary_search_tree(nodes):
    """
    This function calculates and prints the optimal binary search tree.
    The dynamic programming algorithm below runs in O(n^2) time.
    Implemented from CLRS (Introduction to Algorithms) book.
    https://en.wikipedia.org/wiki/Introduction_to_Algorithms

    >>> find_optimal_binary_search_tree([Node(12, 8), Node(10, 34), Node(20, 50), \
                                         Node(42, 3), Node(25, 40), Node(37, 30)])
    Binary search tree nodes:
    Node(key=10, freq=34)
    Node(key=12, freq=8)
    Node(key=20, freq=50)
    Node(key=25, freq=40)
    Node(key=37, freq=30)
    Node(key=42, freq=3)
    <BLANKLINE>
    The cost of optimal BST for given tree nodes is 324.
    20 is the root of the binary search tree.
    10 is the left child of key 20.
    12 is the right child of key 10.
    25 is the right child of key 20.
    37 is the right child of key 25.
    42 is the right child of key 37.
    """
    # Tree nodes must be sorted first, the code below sorts the keys in
    # increasing order and rearrange its frequencies accordingly.
    nodes.sort(key=lambda node: node.key)

    n = len(nodes)

    keys = [nodes[i].key for i in range(n)]
    freqs = [nodes[i].freq for i in range(n)]

    # This 2D array stores the overall tree cost (which's as minimized as possible);
    # for a single key, cost is equal to frequency of the key.
    dp = [[freqs[i] if i == j else 0 for j in range(n)] for i in range(n)]
    # sum[i][j] stores the sum of key frequencies between i and j inclusive in nodes
    # array
    total = [[freqs[i] if i == j else 0 for j in range(n)] for i in range(n)]
    # stores tree roots that will be used later for constructing binary search tree
    root = [[i if i == j else 0 for j in range(n)] for i in range(n)]

    for interval_length in range(2, n + 1):
        for i in range(n - interval_length + 1):
            j = i + interval_length - 1

            dp[i][j] = sys.maxsize  # set the value to "infinity"
            total[i][j] = total[i][j - 1] + freqs[j]

            # Apply Knuth's optimization
            # Loop without optimization: for r in range(i, j + 1):
            for r in range(root[i][j - 1], root[i + 1][j] + 1):  # r is a temporal root
                left = dp[i][r - 1] if r != i else 0  # optimal cost for left subtree
                right = dp[r + 1][j] if r != j else 0  # optimal cost for right subtree
                cost = left + total[i][j] + right

                if dp[i][j] > cost:
                    dp[i][j] = cost
                    root[i][j] = r

    print("Binary search tree nodes:")
    for node in nodes:
        print(node)

    print(f"\nThe cost of optimal BST for given tree nodes is {dp[0][n - 1]}.")
    print_binary_search_tree(root, keys, 0, n - 1, -1, False)
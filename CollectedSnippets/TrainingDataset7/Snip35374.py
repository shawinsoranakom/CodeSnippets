def test_execute_tree(self):
        """
        A visualisation of the callback tree tested. Each node is expected to
        be visited only once:

        └─branch_1
          ├─branch_2
          │ ├─leaf_1
          │ └─leaf_2
          └─leaf_3
        """
        branch_1_call_counter = 0
        branch_2_call_counter = 0
        leaf_1_call_counter = 0
        leaf_2_call_counter = 0
        leaf_3_call_counter = 0

        def leaf_1():
            nonlocal leaf_1_call_counter
            leaf_1_call_counter += 1

        def leaf_2():
            nonlocal leaf_2_call_counter
            leaf_2_call_counter += 1

        def leaf_3():
            nonlocal leaf_3_call_counter
            leaf_3_call_counter += 1

        def branch_1():
            nonlocal branch_1_call_counter
            branch_1_call_counter += 1
            transaction.on_commit(branch_2)
            transaction.on_commit(leaf_3)

        def branch_2():
            nonlocal branch_2_call_counter
            branch_2_call_counter += 1
            transaction.on_commit(leaf_1)
            transaction.on_commit(leaf_2)

        with self.captureOnCommitCallbacks(execute=True) as callbacks:
            transaction.on_commit(branch_1)

        self.assertEqual(branch_1_call_counter, 1)
        self.assertEqual(branch_2_call_counter, 1)
        self.assertEqual(leaf_1_call_counter, 1)
        self.assertEqual(leaf_2_call_counter, 1)
        self.assertEqual(leaf_3_call_counter, 1)

        self.assertEqual(callbacks, [branch_1, branch_2, leaf_3, leaf_1, leaf_2])
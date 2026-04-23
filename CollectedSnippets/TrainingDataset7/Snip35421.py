def branch_2():
            nonlocal branch_2_call_counter
            branch_2_call_counter += 1
            transaction.on_commit(leaf_1)
            transaction.on_commit(leaf_2)
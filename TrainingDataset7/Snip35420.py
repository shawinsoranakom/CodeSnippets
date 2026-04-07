def branch_1():
            nonlocal branch_1_call_counter
            branch_1_call_counter += 1
            transaction.on_commit(branch_2)
            transaction.on_commit(leaf_3)
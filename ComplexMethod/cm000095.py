def main(self, **kwargs) -> None:
        """
        Utilize various methods in this class to simulate the Banker's algorithm
            :Return: None

        >>> BankersAlgorithm(test_claim_vector, test_allocated_res_table,
        ...    test_maximum_claim_table).main(describe=True)
                 Allocated Resource Table
        P1       2        0        1        1
        <BLANKLINE>
        P2       0        1        2        1
        <BLANKLINE>
        P3       4        0        0        3
        <BLANKLINE>
        P4       0        2        1        0
        <BLANKLINE>
        P5       1        0        3        0
        <BLANKLINE>
                 System Resource Table
        P1       3        2        1        4
        <BLANKLINE>
        P2       0        2        5        2
        <BLANKLINE>
        P3       5        1        0        5
        <BLANKLINE>
        P4       1        5        3        0
        <BLANKLINE>
        P5       3        0        3        3
        <BLANKLINE>
        Current Usage by Active Processes: 8 5 9 7
        Initial Available Resources:       1 2 2 2
        __________________________________________________
        <BLANKLINE>
        Process 3 is executing.
        Updated available resource stack for processes: 5 2 2 5
        The process is in a safe state.
        <BLANKLINE>
        Process 1 is executing.
        Updated available resource stack for processes: 7 2 3 6
        The process is in a safe state.
        <BLANKLINE>
        Process 2 is executing.
        Updated available resource stack for processes: 7 3 5 7
        The process is in a safe state.
        <BLANKLINE>
        Process 4 is executing.
        Updated available resource stack for processes: 7 5 6 7
        The process is in a safe state.
        <BLANKLINE>
        Process 5 is executing.
        Updated available resource stack for processes: 8 5 9 7
        The process is in a safe state.
        <BLANKLINE>
        """
        need_list = self.__need()
        alloc_resources_table = self.__allocated_resources_table
        available_resources = self.__available_resources()
        need_index_manager = self.__need_index_manager()
        for kw, val in kwargs.items():
            if kw and val is True:
                self.__pretty_data()
        print("_" * 50 + "\n")
        while need_list:
            safe = False
            for each_need in need_list:
                execution = True
                for index, need in enumerate(each_need):
                    if need > available_resources[index]:
                        execution = False
                        break
                if execution:
                    safe = True
                    # get the original index of the process from ind_ctrl db
                    for original_need_index, need_clone in need_index_manager.items():
                        if each_need == need_clone:
                            process_number = original_need_index
                    print(f"Process {process_number + 1} is executing.")
                    # remove the process run from stack
                    need_list.remove(each_need)
                    # update available/freed resources stack
                    available_resources = np.array(available_resources) + np.array(
                        alloc_resources_table[process_number]
                    )
                    print(
                        "Updated available resource stack for processes: "
                        + " ".join([str(x) for x in available_resources])
                    )
                    break
            if safe:
                print("The process is in a safe state.\n")
            else:
                print("System in unsafe state. Aborting...\n")
                break
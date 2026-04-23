def calculate_waitingtime(
    arrival_time: list[int], burst_time: list[int], no_of_processes: int
) -> list[int]:
    """
    Calculate the waiting time of each processes

    Return: The waiting time for each process.
    >>> calculate_waitingtime([0,1,2], [10, 5, 8], 3)
    [0, 9, 13]
    >>> calculate_waitingtime([1,2,2,4], [4, 6, 3, 1], 4)
    [0, 7, 4, 1]
    >>> calculate_waitingtime([0,0,0], [12, 2, 10],3)
    [12, 0, 2]
    """

    waiting_time = [0] * no_of_processes
    remaining_time = [0] * no_of_processes

    # Initialize remaining_time to waiting_time.

    for i in range(no_of_processes):
        remaining_time[i] = burst_time[i]
    ready_process: list[int] = []

    completed = 0
    total_time = 0

    # When processes are not completed,
    # A process whose arrival time has passed \
    # and has remaining execution time is put into the ready_process.
    # The shortest process in the ready_process, target_process is executed.

    while completed != no_of_processes:
        ready_process = []
        target_process = -1

        for i in range(no_of_processes):
            if (arrival_time[i] <= total_time) and (remaining_time[i] > 0):
                ready_process.append(i)

        if len(ready_process) > 0:
            target_process = ready_process[0]
            for i in ready_process:
                if remaining_time[i] < remaining_time[target_process]:
                    target_process = i
            total_time += burst_time[target_process]
            completed += 1
            remaining_time[target_process] = 0
            waiting_time[target_process] = (
                total_time - arrival_time[target_process] - burst_time[target_process]
            )
        else:
            total_time += 1

    return waiting_time
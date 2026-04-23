def calculate_waitingtime(
    arrival_time: list[int], burst_time: list[int], no_of_processes: int
) -> list[int]:
    """
    Calculate the waiting time of each processes
    Return: List of waiting times.
    >>> calculate_waitingtime([1,2,3,4],[3,3,5,1],4)
    [0, 3, 5, 0]
    >>> calculate_waitingtime([1,2,3],[2,5,1],3)
    [0, 2, 0]
    >>> calculate_waitingtime([2,3],[5,1],2)
    [1, 0]
    """
    remaining_time = [0] * no_of_processes
    waiting_time = [0] * no_of_processes
    # Copy the burst time into remaining_time[]
    for i in range(no_of_processes):
        remaining_time[i] = burst_time[i]

    complete = 0
    increment_time = 0
    minm = 999999999
    short = 0
    check = False

    # Process until all processes are completed
    while complete != no_of_processes:
        for j in range(no_of_processes):
            if (
                arrival_time[j] <= increment_time
                and remaining_time[j] > 0
                and remaining_time[j] < minm
            ):
                minm = remaining_time[j]
                short = j
                check = True

        if not check:
            increment_time += 1
            continue
        remaining_time[short] -= 1

        minm = remaining_time[short]
        if minm == 0:
            minm = 999999999

        if remaining_time[short] == 0:
            complete += 1
            check = False

            # Find finish time of current process
            finish_time = increment_time + 1

            # Calculate waiting time
            finar = finish_time - arrival_time[short]
            waiting_time[short] = finar - burst_time[short]

            waiting_time[short] = max(waiting_time[short], 0)

        # Increment time
        increment_time += 1
    return waiting_time
def _func_cleanup(self, llm_resp: str, prompt: str) -> list:
        # TODO SOMETHING HERE sometimes fails... See screenshot
        temp = [i.strip() for i in llm_resp.split("\n")]
        _cr = []
        cr = []
        for count, i in enumerate(temp):
            if count != 0:
                _cr += [" ".join([j.strip() for j in i.split(" ")][3:])]
            else:
                _cr += [i]
        for count, i in enumerate(_cr):
            k = [j.strip() for j in i.split("(duration in minutes:")]
            task = k[0]
            if task[-1] == ".":
                task = task[:-1]
            duration = int(k[1].split(",")[0].strip())
            cr += [[task, duration]]

        total_expected_min = int(prompt.split("(total duration in minutes")[-1].split("):")[0].strip())

        # TODO -- now, you need to make sure that this is the same as the sum of
        #         the current action sequence.
        curr_min_slot = [
            ["dummy", -1],
        ]  # (task_name, task_index)
        for count, i in enumerate(cr):
            i_task = i[0]
            i_duration = i[1]

            i_duration -= i_duration % 5
            if i_duration > 0:
                for j in range(i_duration):
                    curr_min_slot += [(i_task, count)]
        curr_min_slot = curr_min_slot[1:]

        if len(curr_min_slot) > total_expected_min:
            last_task = curr_min_slot[60]
            for i in range(1, 6):
                curr_min_slot[-1 * i] = last_task
        elif len(curr_min_slot) < total_expected_min:
            last_task = curr_min_slot[-1]
            for i in range(total_expected_min - len(curr_min_slot)):
                curr_min_slot += [last_task]

        cr_ret = [
            ["dummy", -1],
        ]
        for task, task_index in curr_min_slot:
            if task != cr_ret[-1][0]:
                cr_ret += [[task, 1]]
            else:
                cr_ret[-1][1] += 1
        cr = cr_ret[1:]

        return cr
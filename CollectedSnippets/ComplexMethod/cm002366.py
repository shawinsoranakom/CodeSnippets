def post_reply(self):
        if self.thread_ts is None:
            raise ValueError("Can only post reply if a post has been made.")

        sorted_dict = sorted(self.model_results.items(), key=lambda t: t[0])
        for job, job_result in sorted_dict:
            if len(job_result["failures"]):
                for device, failures in job_result["failures"].items():
                    text = "\n".join(
                        sorted([f"*{k}*: {v[device]}" for k, v in job_result["failed"].items() if v[device]])
                    )

                    blocks = self.get_reply_blocks(job, job_result, failures, device, text=text)

                    print("Sending the following reply")
                    print(json.dumps({"blocks": blocks}))

                    client.chat_postMessage(
                        channel=SLACK_REPORT_CHANNEL_ID,
                        text=f"Results for {job}",
                        blocks=blocks,
                        thread_ts=self.thread_ts["ts"],
                    )

                    time.sleep(1)

        for job, job_result in self.additional_results.items():
            if len(job_result["failures"]):
                for device, failures in job_result["failures"].items():
                    blocks = self.get_reply_blocks(
                        job,
                        job_result,
                        failures,
                        device,
                        text=f"Number of failures: {job_result['failed'][device]}",
                    )

                    print("Sending the following reply")
                    print(json.dumps({"blocks": blocks}))

                    client.chat_postMessage(
                        channel=SLACK_REPORT_CHANNEL_ID,
                        text=f"Results for {job}",
                        blocks=blocks,
                        thread_ts=self.thread_ts["ts"],
                    )

                    time.sleep(1)
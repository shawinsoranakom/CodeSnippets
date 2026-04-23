def parse_outputs(self, outputs: list[str], keep_len: int = 5000) -> Tuple[bool, str]:
        """Parses the outputs received from notebook execution."""
        assert isinstance(outputs, list)
        parsed_output, is_success = [], True
        for i, output in enumerate(outputs):
            output_text = ""
            if output["output_type"] == "stream" and not any(
                tag in output["text"]
                for tag in ["| INFO     | metagpt", "| ERROR    | metagpt", "| WARNING  | metagpt", "DEBUG"]
            ):
                output_text = output["text"]
            elif output["output_type"] == "display_data":
                if "image/png" in output["data"]:
                    self.show_bytes_figure(output["data"]["image/png"], self.interaction)
                else:
                    logger.info(
                        f"{i}th output['data'] from nbclient outputs dont have image/png, continue next output ..."
                    )
            elif output["output_type"] == "execute_result":
                output_text = output["data"]["text/plain"]
            elif output["output_type"] == "error":
                output_text, is_success = "\n".join(output["traceback"]), False

            # handle coroutines that are not executed asynchronously
            if output_text.strip().startswith("<coroutine object"):
                output_text = "Executed code failed, you need use key word 'await' to run a async code."
                is_success = False

            output_text = remove_escape_and_color_codes(output_text)
            if is_success:
                output_text = remove_log_and_warning_lines(output_text)
            # The useful information of the exception is at the end,
            # the useful information of normal output is at the begining.
            if "<!DOCTYPE html>" not in output_text:
                output_text = output_text[:keep_len] if is_success else output_text[-keep_len:]

            parsed_output.append(output_text)
        return is_success, ",".join(parsed_output)
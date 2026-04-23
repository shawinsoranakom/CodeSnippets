async def wrapper(self, *args, **kwargs):
        try:
            return await func(self, *args, **kwargs)
        except KeyboardInterrupt as kbi:
            logger.error(f"KeyboardInterrupt: {kbi} occurs, start to serialize the project")
            if self.latest_observed_msg:
                self.rc.memory.delete(self.latest_observed_msg)
            # raise again to make it captured outside
            raise Exception(format_trackback_info(limit=None))
        except Exception as e:
            if self.latest_observed_msg:
                logger.exception(
                    "There is a exception in role's execution, in order to resume, "
                    "we delete the newest role communication message in the role's memory."
                )
                # remove role newest observed msg to make it observed again
                self.rc.memory.delete(self.latest_observed_msg)
            # raise again to make it captured outside
            if isinstance(e, RetryError):
                last_error = e.last_attempt._exception
                name = any_to_str(last_error)
                if re.match(r"^openai\.", name) or re.match(r"^httpx\.", name):
                    raise last_error

            raise Exception(format_trackback_info(limit=None)) from e
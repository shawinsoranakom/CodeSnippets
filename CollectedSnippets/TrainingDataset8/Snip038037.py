def _get_message(self, failed_msg_str: Any) -> str:
        # This needs to have zero indentation otherwise the markdown will render incorrectly.
        return (
            (
                """
**Data of size {message_size_mb:.1f} MB exceeds the message size limit of {message_size_limit_mb} MB.**

This is often caused by a large chart or dataframe. Please decrease the amount of data sent
to the browser, or increase the limit by setting the config option `server.maxMessageSize`.
[Click here to learn more about config options](https://docs.streamlit.io/library/advanced-features/configuration#set-configuration-options).

_Note that increasing the limit may lead to long loading times and large memory consumption
of the client's browser and the Streamlit server._
"""
            )
            .format(
                message_size_mb=len(failed_msg_str) / 1e6,
                message_size_limit_mb=(get_max_message_size_bytes() / 1e6),
            )
            .strip("\n")
        )
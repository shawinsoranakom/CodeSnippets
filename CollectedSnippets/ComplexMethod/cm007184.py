def validate_model(cls, values):
        if not values.get("outputs") and values.get("artifacts"):
            # Build the log from the artifacts

            for key in values["artifacts"]:
                message = values["artifacts"][key]

                # ! Temporary fix
                if message is None:
                    continue

                if "stream_url" in message and "type" in message:
                    stream_url = StreamURL(location=message["stream_url"])
                    values["outputs"].update({key: OutputValue(message=stream_url, type=message["type"])})
                elif "type" in message:
                    values["outputs"].update({key: OutputValue(message=message, type=message["type"])})
        return values
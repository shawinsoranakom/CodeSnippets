def get_queue_attributes(self, attribute_names: AttributeNameList = None) -> dict[str, str]:
        if not attribute_names:
            return {}

        if QueueAttributeName.All in attribute_names:
            attribute_names = list(self.attributes.keys()) + DYNAMIC_ATTRIBUTES

        result: dict[QueueAttributeName, str] = {}

        for attr in attribute_names:
            try:
                getattr(QueueAttributeName, attr)
            except AttributeError:
                raise InvalidAttributeName(f"Unknown Attribute {attr}.")

            # The approximate_* attributes are calculated on the spot when accessed.
            # We have a @property for each of those which calculates the value.
            match attr:
                case QueueAttributeName.ApproximateNumberOfMessages:
                    value = str(self.approximate_number_of_messages)
                case QueueAttributeName.ApproximateNumberOfMessagesDelayed:
                    value = str(self.approximate_number_of_messages_delayed)
                case QueueAttributeName.ApproximateNumberOfMessagesNotVisible:
                    value = str(self.approximate_number_of_messages_not_visible)
                case _:
                    value = self.attributes.get(attr)
            if value == "False" or value == "True":
                result[attr] = value.lower()
            elif value is not None:
                result[attr] = value
        return result
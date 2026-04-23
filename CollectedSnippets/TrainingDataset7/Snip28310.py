def choice(self, obj):
                value, label = super().choice(obj)
                return CustomModelChoiceValue(value, obj), label
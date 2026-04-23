def items(self):
        return I18nTestModel.objects.order_by("pk").all()
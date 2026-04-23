def save_model(self, request, obj, form, change=True):
        EmailMessage(
            "Greetings from a created object",
            "I hereby inform you that some user created me",
            "from@example.com",
            ["to@example.com"],
        ).send()
        return super().save_model(request, obj, form, change)
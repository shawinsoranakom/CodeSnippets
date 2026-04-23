def delete_model(self, request, obj):
        EmailMessage(
            "Greetings from a deleted object",
            "I hereby inform you that some user deleted me",
            "from@example.com",
            ["to@example.com"],
        ).send()
        return super().delete_model(request, obj)
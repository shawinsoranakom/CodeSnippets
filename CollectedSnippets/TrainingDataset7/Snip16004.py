def mail_admin(self, request, selected):
        EmailMessage(
            "Greetings from a ModelAdmin action",
            "This is the test email from an admin action",
            "from@example.com",
            ["to@example.com"],
        ).send()
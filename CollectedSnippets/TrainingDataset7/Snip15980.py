def external_mail(modeladmin, request, selected):
    EmailMessage(
        "Greetings from a function action",
        "This is the test email from a function action",
        "from@example.com",
        ["to@example.com"],
    ).send()
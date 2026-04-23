def mail_sending_view(request):
    mail.EmailMessage(
        "Test message",
        "This is a test email",
        "from@example.com",
        ["first@example.com", "second@example.com"],
    ).send()
    return HttpResponse("Mail sent")
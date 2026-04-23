def mass_mail_sending_view(request):
    m1 = mail.EmailMessage(
        "First Test message",
        "This is the first test email",
        "from@example.com",
        ["first@example.com", "second@example.com"],
    )
    m2 = mail.EmailMessage(
        "Second Test message",
        "This is the second test email",
        "from@example.com",
        ["second@example.com", "third@example.com"],
    )

    c = mail.get_connection()
    c.send_messages([m1, m2])

    return HttpResponse("Mail sent")
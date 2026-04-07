def handle(self, *args, **kwargs):
        subject = "Test email from %s on %s" % (socket.gethostname(), timezone.now())

        send_mail(
            subject=subject,
            message="If you're reading this, it was successful.",
            from_email=None,
            recipient_list=kwargs["email"],
        )

        if kwargs["managers"]:
            mail_managers(subject, "This email was sent to the site managers.")

        if kwargs["admins"]:
            mail_admins(subject, "This email was sent to the site admins.")
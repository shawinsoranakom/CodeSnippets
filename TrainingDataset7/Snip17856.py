def send_mail(
                self,
                subject_template_name,
                email_template_name,
                context,
                from_email,
                to_email,
                html_email_template_name=None,
            ):
                EmailMultiAlternatives(
                    "Forgot your password?",
                    "Sorry to hear you forgot your password.",
                    None,
                    [to_email],
                    bcc=["site_monitor@example.com"],
                    headers={"Reply-To": "webmaster@example.com"},
                    alternatives=[
                        ("Really sorry to hear you forgot your password.", "text/html")
                    ],
                ).send()
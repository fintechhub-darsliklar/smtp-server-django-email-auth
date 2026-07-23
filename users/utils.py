import threading
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.core.mail import EmailMultiAlternatives
from django.conf import settings

# Ichki umumiy yuboruvchi oqim (Thread) klassi
class EmailThread(threading.Thread):
    def __init__(self, subject, template_name, context, recipient_email):
        self.subject = subject
        self.template_name = template_name
        self.context = context
        self.recipient_email = recipient_email
        super().__init__()

    def run(self):
        try:
            html_content = render_to_string(self.template_name, self.context)
            text_content = strip_tags(html_content)

            msg = EmailMultiAlternatives(
                self.subject,
                text_content,
                settings.DEFAULT_FROM_EMAIL,
                [self.recipient_email]
            )
            msg.attach_alternative(html_content, "text/html")
            msg.send()
        except Exception as e:
            print(f"Email yuborishda xatolik ({self.recipient_email}): {e}")


# 1. Emailni tasdiqlash uchun (Background)
def send_verification_email(user, token, request):
    domain = request.get_host()
    protocol = 'https' if request.is_secure() else 'http'
    verify_url = f"{protocol}://{domain}/verify/?token={token}"

    subject = 'Email manzilingizni tasdiqlang'
    context = {
        'user': user,
        'verify_url': verify_url,
    }
    
    # Thread'ni ishga tushiramiz
    EmailThread(subject, 'verifi-token.html', context, user.email).start()


# 2. Parolni tiklash uchun (Background)
def send_verification_email_forget_password(user, token, request):
    domain = request.get_host()
    protocol = 'https' if request.is_secure() else 'http'
    verify_url = f"{protocol}://{domain}/forget-password-verify/?token={token}"

    subject = 'Parolni qayta tiklash'
    context = {
        'user': user,
        'forget_password_verify_url': verify_url,
    }
    
    # Thread'ni ishga tushiramiz
    EmailThread(subject, 'forget-password/mail-send.html', context, user.email).start()
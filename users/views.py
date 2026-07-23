from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from users.forms import LoginForm, RegisterForm
from django.contrib.auth import login, logout
from users.models import User, VerificationsLink

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.utils import timezone
from datetime import timedelta


# ------------- Home page --------------


def send_verification_email(user, token, request):
    domain = request.get_host()
    protocol = 'https' if request.is_secure() else 'http'
    verify_url = f"{protocol}://{domain}/verify/?token={token}"

    subject = 'Email manzilingizni tasdiqlang'
    
    context = {
        'user': user,
        'verify_url': verify_url,
    }
    
    html_content = render_to_string('verifi-token.html', context)
    text_content = strip_tags(html_content)

    msg = EmailMultiAlternatives(
        subject,
        text_content,
        settings.DEFAULT_FROM_EMAIL,
        [user.email]
    )
    msg.attach_alternative(html_content, "text/html")
    msg.send()

@login_required
def home_page(request):
    return render(request, 'home.html')


# ------------- Auth page --------------


def login_page(request):
    error = ""
    if request.method == "POST":
        data = request.POST
        email = data.get("email", "").strip()
        password = data.get("password", "").strip()
        if email and password:
            try:
                user = User.objects.get(email=email)
            except:
                user = None
                error = "User topilmadi!"
            if user:
                check_password = user.check_password(password)
                if check_password:
                    if user.is_active:
                        login(request, user)
                        return redirect("home_page")
                    else:
                        error = "User aktiv emas"
                else:
                    error = "Parol yoki email xato"
    context = {
        "form": LoginForm(),
        "error": error
    }
    return render(request, 'login.html', context=context)

def logout_page(request):
    logout(request)
    return redirect("login_page")

def register_page(request):
    error = ""
    if request.method == "POST":
        data = request.POST
        first_name = data.get("first_name", "").strip()
        email = data.get("email", "").strip()
        password = data.get("password", "").strip()
        password_confirm = data.get("password_confirm", "").strip()
        if len(first_name) > 2 and len(password) > 8 and email:
            if password != password_confirm:
                error = "Parollar mos emas!"
            else:
                user = User.objects.filter(email=email)
                if user.exists():
                    error = "Bu emaildagi user allaqachon mavjud!"
                else:
                    user = User.objects.create(
                        first_name=first_name,
                        email=email,
                        password=password,
                        is_active=False
                    )
                    user.set_password(password)
                    user.save()
                    verifi = VerificationsLink.objects.create(
                        user=user
                    )
                    send_verification_email(user, verifi.token, request)
                    return redirect("send_link_mail")

    context = {
        "form": RegisterForm(),
        "error": error
    }
    return render(request, 'register.html', context=context)


# ------------- Verification account --------------


def send_link_mail(request):
    return render(request, "verifi-token-send.html")

def verifi_account_page(request):
    token = request.GET.get('token')
    try:
        token = VerificationsLink.objects.get(token=token)
    except:
        token = None
    if token:
        if timezone.now() < token.expired_at:
            token.user.is_active = True
            token.user.save()
            token.expired_at = timezone.now()
            token.save()
            return render(request, "verifi-token-confirm.html")
        else:
            return render(request, "verifi-resend.html", context={"user_token": token.token})
    return redirect("login_page")

def resend_mail(request, token):
    try:
        token = VerificationsLink.objects.get(token=token)
    except:
        token = None
    if token:
        if timezone.now() > token.expired_at:
            print(token)
            new_token = VerificationsLink.objects.create(
                user=token.user
            )
            send_verification_email(token.user, new_token.token, request)
            return redirect("send_link_mail")
        return render(request, 'verifi-token-active.html', context={"user_token": token.token})
    return redirect('login_page')


# ------------- Forget password --------------


def send_verification_email_forget_password(user, token, request):
    domain = request.get_host()
    protocol = 'https' if request.is_secure() else 'http'
    verify_url = f"{protocol}://{domain}/forget-password-verify/?token={token}"

    subject = 'Parolni qayta tiklash'
    
    context = {
        'user': user,
        'forget_password_verify_url': verify_url,
    }
    
    html_content = render_to_string('forget-password/mail-send.html', context)
    text_content = strip_tags(html_content)

    msg = EmailMultiAlternatives(
        subject,
        text_content,
        settings.DEFAULT_FROM_EMAIL,
        [user.email]
    )
    msg.attach_alternative(html_content, "text/html")
    msg.send()

def forget_password_page(request):

    if request.method == "POST":
        email = request.POST.get("email")
        try:
            user = User.objects.get(email=email)
        except:
            user = None
        if user:
            token = VerificationsLink.objects.create(user=user)
            send_verification_email_forget_password(user, token.token, request)
            return redirect('forget_password_send_page')
    return render(request, 'forget-password/forget-password.html')

def forget_password_send_page(request):
    return render(request, 'forget-password/verifi-token-send.html')

def forget_password_verifi_page(request):
    error = ""
    if request.method == "POST":
        data = request.POST
        token = data.get("token")
        new_password1 = data.get("new_password1")
        new_password2 = data.get("new_password2")
        if token and new_password1 and new_password2:
            if new_password1 != new_password2:
                error = "Parollar mos emas!"
            else:
                try:
                    token = VerificationsLink.objects.get(token=token)
                except:
                    token = None
                if token:
                    if timezone.now() < token.expired_at:
                        token.expired_at = timezone.now()
                        token.save()
                        token.user.set_password(new_password1)
                        token.user.save()
                        return redirect("login_page")
    
    token = request.GET.get('token')
    try:
        token = VerificationsLink.objects.get(token=token)
    except:
        token = None
    if token:
        if timezone.now() < token.expired_at:
            token.expired_at = timezone.now() + timedelta(minutes=15)
            token.save()
            return render(request, "forget-password/password-new.html", context={"token": token.token, "error": error})

    return redirect("login_page")


from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from users.forms import LoginForm, RegisterForm
from django.contrib.auth import login, logout, update_session_auth_hash
from users.models import User, VerificationsLink, ActionToken

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.utils import timezone
from datetime import timedelta, datetime
import smtplib


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
    try:
        msg.send()
        return True
    except (OSError, smtplib.SMTPException):
        return False

@login_required
def home_page(request):
    return render(request, 'home.html')


# ------------- Profile page --------------

def send_email_change_confirmation(user, new_email, token, request):
    domain = request.get_host()
    protocol = 'https' if request.is_secure() else 'http'
    confirm_url = f"{protocol}://{domain}/confirm-email-change/?token={token}"

    subject = 'Yangi emailni tasdiqlang'

    context = {
        'user': user,
        'new_email': new_email,
        'confirm_url': confirm_url,
    }

    html_content = render_to_string('change-email/mail-send.html', context)
    text_content = strip_tags(html_content)

    msg = EmailMultiAlternatives(
        subject,
        text_content,
        settings.DEFAULT_FROM_EMAIL,
        [new_email]
    )
    msg.attach_alternative(html_content, "text/html")
    try:
        msg.send()
        return True
    except (OSError, smtplib.SMTPException):
        return False


def send_account_delete_confirmation(user, token, request):
    domain = request.get_host()
    protocol = 'https' if request.is_secure() else 'http'
    confirm_url = f"{protocol}://{domain}/confirm-account-delete/?token={token}"

    subject = 'Hisobni o\'chirishni tasdiqlang'

    context = {
        'user': user,
        'confirm_url': confirm_url,
    }

    html_content = render_to_string('account-delete/mail-send.html', context)
    text_content = strip_tags(html_content)

    msg = EmailMultiAlternatives(
        subject,
        text_content,
        settings.DEFAULT_FROM_EMAIL,
        [user.email]
    )
    msg.attach_alternative(html_content, "text/html")
    try:
        msg.send()
        return True
    except (OSError, smtplib.SMTPException):
        return False


@login_required
def profile_page(request):
    error = ""
    success = ""
    if request.method == "POST":
        action = request.POST.get("action")

        if action == "update_profile":
            first_name = request.POST.get("first_name", "").strip()
            last_name = request.POST.get("last_name", "").strip()
            birth_date = request.POST.get("birth_date", "").strip()
            if len(first_name) > 2:
                request.user.first_name = first_name
                request.user.last_name = last_name
                if birth_date:
                    try:
                        request.user.birth_date = datetime.strptime(birth_date, "%Y-%m-%d").date()
                    except ValueError:
                        request.user.birth_date = None
                else:
                    request.user.birth_date = None
                request.user.save()
                success = "Profil ma'lumotlari yangilandi!"
            else:
                error = "Ism kamida 3 ta belgidan iborat bo'lishi kerak!"

        elif action == "change_password":
            old_password = request.POST.get("old_password", "").strip()
            new_password1 = request.POST.get("new_password1", "").strip()
            new_password2 = request.POST.get("new_password2", "").strip()
            if not request.user.check_password(old_password):
                error = "Joriy parol xato!"
            elif len(new_password1) < 8:
                error = "Yangi parol kamida 8 ta belgidan iborat bo'lishi kerak!"
            elif new_password1 != new_password2:
                error = "Yangi parollar mos emas!"
            else:
                request.user.set_password(new_password1)
                request.user.save()
                update_session_auth_hash(request, request.user)
                success = "Parol muvaffaqiyatli o'zgartirildi!"

        elif action == "change_email":
            new_email = request.POST.get("new_email", "").strip().lower()
            if not new_email:
                error = "Yangi email kiriting!"
            elif new_email == request.user.email:
                error = "Bu sizning joriy emailingiz!"
            elif User.objects.filter(email=new_email).exists():
                error = "Bu email allaqachon boshqa hisobda ro'yxatdan o'tgan!"
            else:
                action_token = ActionToken.objects.create(
                    user=request.user,
                    purpose=ActionToken.Purpose.EMAIL_CHANGE,
                    new_email=new_email,
                )
                if send_email_change_confirmation(request.user, new_email, action_token.token, request):
                    success = f"Tasdiqlash havolasi {new_email} manziliga yuborildi. Emailingizni tekshiring!"
                else:
                    action_token.delete()
                    error = "Email yuborib bo'lmadi. Birozdan so'ng qayta urinib ko'ring."

        elif action == "delete_account":
            action_token = ActionToken.objects.create(
                user=request.user,
                purpose=ActionToken.Purpose.ACCOUNT_DELETE,
            )
            if send_account_delete_confirmation(request.user, action_token.token, request):
                success = "Hisobni o'chirishni tasdiqlash havolasi emailingizga yuborildi!"
            else:
                action_token.delete()
                error = "Email yuborib bo'lmadi. Birozdan so'ng qayta urinib ko'ring."

    context = {
        "error": error,
        "success": success,
    }
    return render(request, 'profile.html', context)


# ------------- Confirm email change / account delete --------------

def confirm_email_change_page(request):
    token = request.GET.get('token')
    try:
        action_token = ActionToken.objects.get(token=token, purpose=ActionToken.Purpose.EMAIL_CHANGE)
    except ActionToken.DoesNotExist:
        action_token = None

    if action_token:
        if timezone.now() < action_token.expired_at:
            if User.objects.filter(email=action_token.new_email).exclude(pk=action_token.user_id).exists():
                action_token.delete()
                return render(request, "change-email/email-taken.html")
            action_token.user.email = action_token.new_email
            action_token.user.save()
            action_token.delete()
            return render(request, "change-email/email-confirmed.html")
        action_token.delete()

    return render(request, "change-email/link-expired.html")


def confirm_account_delete_page(request):
    token = request.GET.get('token')
    try:
        action_token = ActionToken.objects.get(token=token, purpose=ActionToken.Purpose.ACCOUNT_DELETE)
    except ActionToken.DoesNotExist:
        action_token = None

    if action_token:
        if timezone.now() < action_token.expired_at:
            user = action_token.user
            if request.user.is_authenticated and request.user.pk == user.pk:
                logout(request)
            action_token.delete()
            user.delete()
            return render(request, "account-delete/account-deleted.html")
        action_token.delete()

    return render(request, "account-delete/link-expired.html")


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
                    return render(request, "verifi-token-send.html", context={"token":verifi.token})

    context = {
        "form": RegisterForm(),
        "error": error
    }
    return render(request, 'register.html', context=context)


# ------------- Verification account --------------

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
            return render(request, "verifi-token-send.html", context={"token": token.token})

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
    try:
        msg.send()
        return True
    except (OSError, smtplib.SMTPException):
        return False

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


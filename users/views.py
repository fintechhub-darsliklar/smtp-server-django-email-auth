from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from users.forms import LoginForm, RegisterForm
from django.contrib.auth import login
from users.models import User



@login_required
def home_page(request):
    return render(request, 'home.html')

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
                        is_active=True
                    )
                    user.set_password(password)
                    user.save()
                    login(request, user)
                    return redirect("home_page")

    context = {
        "form": RegisterForm(),
        "error": error
    }
    return render(request, 'register.html', context=context)
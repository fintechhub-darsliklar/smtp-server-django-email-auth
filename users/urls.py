from django.urls import path
from users.views import home_page, login_page, register_page


urlpatterns = [
    path("", home_page, name="home_page"),
    path("login/", login_page, name="login_page"),
    path("register/", register_page, name="register_page"),
]

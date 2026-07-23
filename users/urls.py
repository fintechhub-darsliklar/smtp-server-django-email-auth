from django.urls import path
from users.views import home_page, login_page, \
    register_page, verifi_account_page, \
    resend_mail, logout_page, \
    forget_password_page, forget_password_verifi_page, \
    forget_password_send_page


urlpatterns = [
    path("", home_page, name="home_page"),
    path("login/", login_page, name="login_page"),
    path("logout/", logout_page, name="logout_page"),
    path("register/", register_page, name="register_page"),
    path("verify/", verifi_account_page, name="verifi_account_page"),
    path("resend-mail/<str:token>/", resend_mail, name="resend_mail"),

    # forget password
    path("forget-password/", forget_password_page, name="forget_password_page"),
    path("forget-password-verify/", forget_password_verifi_page, name="forget_password_verifi_page"),
    path("forget-password-send/", forget_password_send_page, name="forget_password_send_page"),

]

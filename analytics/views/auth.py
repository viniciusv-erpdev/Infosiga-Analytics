from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.models import AnonymousUser
from django.contrib.auth.views import LoginView, LogoutView
from django.shortcuts import redirect, render


class BootstrapAuthenticationForm(AuthenticationForm):
    error_messages = {
        **AuthenticationForm.error_messages,
        "invalid_login": "Por favor, entre com um usuário e senha corretos.",
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].widget.attrs.update({"class": "form-control"})
        self.fields["password"].widget.attrs.update({"class": "form-control"})


class BootstrapUserCreationForm(UserCreationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].widget.attrs.update({"class": "form-control"})
        self.fields["username"].error_messages["unique"] = "Este nome de usuário já existe"
        self.fields["password1"].widget.attrs.update({"class": "form-control"})
        self.fields["password2"].widget.attrs.update({"class": "form-control"})


class CustomLoginView(LoginView):
    template_name = "analytics/auth/login.html"
    redirect_authenticated_user = True
    authentication_form = BootstrapAuthenticationForm


class CustomLogoutView(LogoutView):
    next_page = "login"
    http_method_names = ["get", "post", "options", "head"]

    def dispatch(self, request, *args, **kwargs):
        logout(request)
        request.user = AnonymousUser()
        return redirect(self.get_default_redirect_url())


def register(request):
    if request.method == "POST":
        form = BootstrapUserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Conta criada com sucesso. Faça login para continuar.")
            return redirect("login")
    else:
        form = BootstrapUserCreationForm()

    return render(request, "analytics/auth/register.html", {"form": form})

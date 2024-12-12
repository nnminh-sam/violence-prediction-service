from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib.auth import login as auth_login, authenticate
from .forms import RegistrationForm, LoginForm


def home(request):
    return render(request, 'home.html')


def register(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            first_name = form.cleaned_data['first_name']
            last_name = form.cleaned_data['last_name']

            user = User.objects.create_user(
                username=email.split('@')[0],
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name
            )

            print('Created new user:', user)
            auth_login(request, user)
            return redirect('home')
    else:
        form = RegistrationForm()

    return render(request, 'register.html', {'form': form})


def user_login(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']

            # Authenticate the user using Django's authentication system
            user = authenticate(request, username=email, password=password)
            if user is not None:
                # Log the user in
                auth_login(request, user)
                return redirect('home')
            else:
                # Add error if authentication fails
                form.add_error(None, "Invalid email or password")

    else:
        form = LoginForm()

    return render(request, 'login.html', {'form': form})

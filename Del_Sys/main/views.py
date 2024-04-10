from django.shortcuts import render,redirect
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from allauth.socialaccount.models import SocialAccount
from django.urls import reverse
from django.contrib import messages
from . import forms

# Create your views here.

def home(request):
    return render(request,"home.html")

def sign_up(request):
    form=forms.SignUpForm()

    if request.method=='POST':
        form=forms.SignUpForm(request.POST)

        if form.is_valid():
            email=form.cleaned_data.get('email').lower()
            user=form.save(commit=False)
            user.username=email
            user.save()         

            login(request,user,backend='django.contrib.auth.backends.ModelBackend')
            return redirect('/')

    return render(request,"sign_up.html",
        {
            'form':form
        }
    )

def google_login(request):
    # Redirect the user to Google authentication URL
    return redirect(reverse('social:begin', args=['google']))


def google_callback(request):
    messages.success(request, 'Successfully logged in with Google.')
    return redirect('/')

# def google_login(request):
#     return redirect('sign_in', 'google')

# def google_callback(request):
#     # Get the user from the social account
#     social_account = SocialAccount.objects.filter(provider='google', user=request.user).first()
#     if social_account:
#         # If the social account exists, log in the user
#         login(request, social_account.user)
#         return redirect('/')  # Redirect to home page or any other desired URL
#     else:
#         return redirect('/sign_in/')  # Redirect to sign-in page if the social account does not exist
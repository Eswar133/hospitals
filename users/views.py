from django.shortcuts import render, redirect
from django.contrib.auth import login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.hashers import make_password
from .models import User

def signup(request):
    if request.method == 'POST':
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        profile_picture = request.FILES.get('profile_picture')
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        address_line1 = request.POST.get('address_line1')
        city = request.POST.get('city')
        state = request.POST.get('state')
        pincode = request.POST.get('pincode')
        user_type = request.POST.get('user_type')
        
        if password == confirm_password:
            user = User(
                first_name=first_name,
                last_name=last_name,
                profile_picture=profile_picture,
                username=username,
                email=email,
                password=make_password(password),
                address_line1=address_line1,
                city=city,
                state=state,
                pincode=pincode,
                user_type=user_type
            )
            user.save()
            auth_login(request, user)
            return redirect('login')
        else:
            error_message = "Passwords do not match."
    else:
        error_message = None

    return render(request, 'signup.html', {'error_message': error_message})

class CustomLoginView(LoginView):
    template_name = 'login.html'
    form_class = AuthenticationForm

    def form_valid(self, form):
        user_type = self.request.POST.get('user_type')
        user = form.get_user()

        if user_type == 'patient':
            # Redirect to patient dashboard
            return redirect('patient_dashboard')
        elif user_type == 'doctor':
            # Redirect to doctor dashboard
            return redirect('doctor_dashboard')
        else:
            # Handle case where user type is not provided or invalid
            return redirect('login')

    def form_invalid(self, form):
        # Handle invalid form submission
        return self.form_invalid(form)
    

def dashboard(request, user_type=None):
    user = request.user
    if user_type is None:
        user_type = user.user_type
    return render(request, f'users/{user_type}_dashboard.html', {
        'user': user,
        'profile_picture_url': user.profile_picture.url if user.profile_picture else None
    })

def logout(request):
    auth_logout(request)
    return redirect('login')
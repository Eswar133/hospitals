from django.shortcuts import render, redirect
from django.contrib.auth import login as auth_login, logout as auth_logout
from django.http import JsonResponse
from django.views import View
from django.contrib.auth.hashers import make_password
from .models import User


class SignupView(View):
    def get(self, request):
        return render(request, 'signup.html', {'error_message': None})

    def post(self, request):
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
        
        if password != confirm_password:
            return JsonResponse({'error_message': 'Passwords do not match.'})
        
        # Check if username or email already exists
        if User.objects.filter(username=username).exists() or User.objects.filter(email=email).exists():
            return JsonResponse({'error_message': 'Username or email already exists.'})

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
        return JsonResponse({'redirect': '/login/'})

class LoginView(View):
    def get(self, request):
        return render(request, 'login.html', {'error_message': None})

    def post(self, request):
        username = request.POST.get('username')
        password = request.POST.get('password')
        user_type = request.POST.get('user_type')

        try:
            user = User.objects.get(username=username)
            if user.check_password(password) and user.user_type == user_type:
                auth_login(request, user)
                return JsonResponse({'redirect': f'/{user_type}_dashboard/'})
            else:
                return JsonResponse({'error_message': 'Invalid credentials.'})
        except User.DoesNotExist:
            return JsonResponse({'error_message': 'User does not exist.'})



class DashboardView(View):
    user_type = None

    def get(self, request):
        user = request.user
        profile_picture_url = user.profile_picture.url if user.profile_picture else 'default-profile-pic-url.jpg'
        
        if self.user_type == 'patient':
            return render(request, 'users/patient_dashboard.html', {
                'user': user,
                'profile_picture_url': profile_picture_url
            })
        elif self.user_type == 'doctor':
            return render(request, 'users/doctor_dashboard.html', {
                'user': user,
                'profile_picture_url': profile_picture_url
            })
        else:
            return redirect('login')

class LogoutView(View):
    def get(self, request):
        auth_logout(request)
        return redirect('login')

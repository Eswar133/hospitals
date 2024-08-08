import os
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login as auth_login, logout as auth_logout
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.views import View
from django.views.generic import ListView, DetailView
from django.contrib.auth.hashers import make_password
from django.core.paginator import Paginator
from django.db.models import Count
from .models import User, BlogPost, Appointment
from datetime import datetime, timedelta
from .utils import send_email_with_calendar_invite, create_ics_file
from django.utils import timezone
from django.conf import settings
from django.core.mail import EmailMessage
from django.utils.html import strip_tags
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build


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

        try:
            user = User.objects.get(username=username)
            if user.check_password(password): 
                auth_login(request, user)
                return JsonResponse({'redirect': f'/'})
            else:
                return JsonResponse({'error_message': 'Invalid credentials.'})
        except User.DoesNotExist:
            return JsonResponse({'error_message': 'Username or Password are incorrect.'})

class DashboardView(LoginRequiredMixin, View):
    def get(self, request):
        user = request.user
        profile_picture_url = user.profile_picture.url if user.profile_picture else 'default-profile-pic-url.jpg'
        
        if user.user_type == 'patient':
            return render(request, 'users/patient_dashboard.html', {
                'user': user,
                'profile_picture_url': profile_picture_url
            })
        elif user.user_type == 'doctor':
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
    
class BlogListView(ListView):
    model = BlogPost
    template_name = 'blog_list.html'
    context_object_name = 'page_obj'
    paginate_by = 10  # Number of posts per page

    def get_queryset(self):
        search_query = self.request.GET.get('query', '')
        sort_by = self.request.GET.get('sort', 'date')
        category = self.kwargs.get('category', None)

        posts = BlogPost.objects.filter(is_draft=False)

        if category:
            posts = posts.filter(category=category)

        if search_query:
            posts = posts.filter(title__icontains=search_query) | posts.filter(author__username__icontains=search_query)

        if sort_by == 'likes':
            posts = posts.annotate(like_count=Count('likes')).order_by('-like_count')
        else:
            posts = posts.order_by('-created_at')
            
        return posts
        
    def truncate_words(self,value, num_words):
        words = value.split()
        if len(words) > num_words:
            return ' '.join(words[:num_words]) + '...'
        return value    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['sort_by'] = self.request.GET.get('sort', 'date')
        context['query'] = self.request.GET.get('query', '')
        context['category'] = self.kwargs.get('category', None)
        user = self.request.user
        context['profile_picture_url'] = user.profile_picture.url if user.profile_picture else 'default-profile-pic-url.jpg'
        
        # Add pagination information
        paginator = Paginator(self.get_queryset(), self.paginate_by)
        page_number = self.request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        context['page_obj'] = page_obj
        for obj in page_obj:
            obj.summary = self.truncate_words(obj.summary, 15)
        
        context['user_type'] = self.request.user.user_type
        return context

class BlogDetailView(DetailView):
    model = BlogPost
    template_name = 'blog_detail.html'
    context_object_name = 'post'
    
    def get_queryset(self):
        return BlogPost.objects.filter(is_draft=False)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        if user.is_authenticated:
            try:
                context['profile_picture_url'] = user.profile_picture.url
            except AttributeError:
                context['profile_picture_url'] = None
        else:
            context['profile_picture_url'] = None
        return context

class AddBlogPostView(View):
    def get(self, request):
        user = request.user
        context = {
            'categories': BlogPost.CATEGORY_CHOICES,
            'profile_picture_url': None
        }
        if user.is_authenticated:
            try:
                context['profile_picture_url'] = user.profile_picture.url
            except AttributeError:
                context['profile_picture_url'] = None
        return render(request, 'add_blog_post.html', context)

    def post(self, request):
        title = request.POST.get('title')
        image = request.FILES.get('image')
        category = request.POST.get('category')
        summary = request.POST.get('summary')
        content = request.POST.get('content')
        is_draft = request.POST.get('is_draft') == 'on'

        blog_post = BlogPost(
            author=request.user,
            title=title,
            image=image,
            category=category,
            summary=summary,
            content=content,
            is_draft=is_draft
        )
        blog_post.save()
        return redirect('/')

class EditBlogPostView(View):
    def get(self, request, pk):
        post = get_object_or_404(BlogPost, pk=pk, author=request.user)
        context = {
            'post': post,
            'categories': BlogPost.CATEGORY_CHOICES,
            'profile_picture_url': None
        }
        if request.user.is_authenticated:
            try:
                context['profile_picture_url'] = request.user.profile_picture.url
            except AttributeError:
                context['profile_picture_url'] = None
        return render(request, 'edit_blog_post.html', context)

    def post(self, request, pk):
        post = get_object_or_404(BlogPost, pk=pk, author=request.user)
        post.title = request.POST.get('title')
        post.image = request.FILES.get('image', post.image)
        post.category = request.POST.get('category')
        post.summary = request.POST.get('summary')
        post.content = request.POST.get('content')
        post.is_draft = request.POST.get('is_draft') == 'on'
        post.save()
        return redirect('/')

class LikeBlogPostView(View):
    def post(self, request, pk):
        post = get_object_or_404(BlogPost, pk=pk)
        if request.user in post.likes.all():
            post.likes.remove(request.user)
        else:
            post.likes.add(request.user)
        return JsonResponse({'likes_count': post.likes.count()})

class DraftListView(LoginRequiredMixin, ListView):
    model = BlogPost
    template_name = 'draft_list.html'
    context_object_name = 'drafts'
    paginate_by = 10  # Adjust the number of drafts per page

    def get_queryset(self):
        return BlogPost.objects.filter(author=self.request.user, is_draft=True)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        if user.is_authenticated:
            try:
                context['profile_picture_url'] = user.profile_picture.url
            except AttributeError:
                context['profile_picture_url'] = None
        else:
            context['profile_picture_url'] = None
        return context
      
class PostedBlogListView(LoginRequiredMixin, ListView):
    model = BlogPost
    template_name = 'posted_blog_list.html'
    context_object_name = 'blogs'
    paginate_by = 10  # Number of blogs per page

    def get_queryset(self):
        return BlogPost.objects.filter(author=self.request.user, is_draft=False)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        if user.is_authenticated:
            try:
                context['profile_picture_url'] = user.profile_picture.url
            except AttributeError:
                context['profile_picture_url'] = None
        else:
            context['profile_picture_url'] = None
        return context
    
class DoctorListView(LoginRequiredMixin, ListView):
    model = User
    template_name = 'doctor_list.html'
    context_object_name = 'doctors'

    def get_queryset(self):
        return User.objects.filter(user_type='doctor')
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        if user.is_authenticated:
            try:
                context['profile_picture_url'] = user.profile_picture.url
            except AttributeError:
                context['profile_picture_url'] = 'default-profile-pic-url.jpg'
        else:
            context['profile_picture_url'] = 'default-profile-pic-url.jpg'
        return context


class BookAppointmentView(View):
    def get(self, request, pk):
        doctor = get_object_or_404(User, pk=pk, user_type='doctor')
        return render(request, 'book_appointment.html', {'doctor': doctor})

    def post(self, request, pk):
        doctor = get_object_or_404(User, pk=pk, user_type='doctor')
        speciality = request.POST.get('speciality')
        appointment_date = request.POST.get('appointment_date')
        start_time = request.POST.get('start_time')

        if not all([speciality, appointment_date, start_time]):
            return JsonResponse({'error': 'All fields are required.'}, status=400)

        # Parse the appointment date and start time
        appointment_date_obj = datetime.strptime(appointment_date, '%Y-%m-%d').date()
        start_time_obj = datetime.strptime(start_time, '%H:%M').time()
        appointment_datetime_naive = datetime.combine(appointment_date_obj, start_time_obj)

        # Convert the naive datetime to an aware datetime
        appointment_datetime = timezone.make_aware(appointment_datetime_naive, timezone.get_current_timezone())

        # Check if the appointment datetime is in the past
        if appointment_datetime <= timezone.now():
            return JsonResponse({'error': 'Cannot book an appointment in the past.'}, status=400)

        end_time = (appointment_datetime + timedelta(minutes=45)).time()

        appointment = Appointment.objects.create(
            patient=request.user,
            doctor=doctor,
            speciality=speciality,
            appointment_date=appointment_datetime.date(),
            start_time=appointment_datetime.time(),
            end_time=end_time
        )

        # Send email confirmation
        self.send_appointment_email(appointment)

        return JsonResponse({'message': 'Appointment booked successfully!'})

    def create_ics_file(self, appointment):
        # Create a calendar instance
        cal = Calendar()

        # Create an event instance
        event = Event()
        event.name = f"Appointment with Dr. {appointment.doctor.get_full_name()}"
        event.begin = datetime.combine(appointment.appointment_date, appointment.start_time)
        event.end = datetime.combine(appointment.appointment_date, appointment.end_time)
        event.description = f"Appointment with Dr. {appointment.doctor.get_full_name()} - Speciality: {appointment.speciality}"

        # Add event to the calendar
        cal.events.add(event)

        # Create a file-like object to store the .ics content
        ics_file = io.BytesIO()
        ics_file.write(str(cal).encode('utf-8'))
        ics_file.seek(0)  # Rewind the file pointer to the beginning

        return ics_file

    def send_appointment_email(self, appointment):
        context = {
            'patient_name': f"{appointment.patient.first_name} {appointment.patient.last_name}",
            'doctor_name': f"{appointment.doctor.first_name} {appointment.doctor.last_name}",
            'speciality': appointment.speciality,
            'date': appointment.appointment_date.strftime("%b. %d, %Y"),
            'start_time': appointment.start_time.strftime("%I:%M %p"),
            'end_time': appointment.end_time.strftime("%I:%M %p"),
        }
        html_content = render_to_string('appointment_email.html', context)
        text_content = strip_tags(html_content)  # Fallback to plain text content

        # Create .ics file
        ics_file = self.create_ics_file(appointment)

        # Send the email with .ics attachment
        email = EmailMessage(
            'Appointment Confirmation',
            text_content,
            'your_email@example.com',  # From email
            [appointment.patient.email],  # To email
        )
        email.content_subtype = 'html'  # Set the primary content to be HTML
        email.attach('appointment.ics', ics_file.read(), 'text/calendar')
        email.send()

class BookAppointmentView(View):
    def get(self, request, pk):
        doctor = get_object_or_404(User, pk=pk, user_type='doctor')
        return render(request, 'book_appointment.html', {'doctor': doctor})

    def post(self, request, pk):
        doctor = get_object_or_404(User, pk=pk, user_type='doctor')
        speciality = request.POST.get('speciality')
        appointment_date = request.POST.get('appointment_date')
        start_time = request.POST.get('start_time')

        if not all([speciality, appointment_date, start_time]):
            return JsonResponse({'error': 'All fields are required.'}, status=400)

        # Parse the appointment date and start time
        appointment_date_obj = datetime.strptime(appointment_date, '%Y-%m-%d').date()
        start_time_obj = datetime.strptime(start_time, '%H:%M').time()
        appointment_datetime_naive = datetime.combine(appointment_date_obj, start_time_obj)

        # Convert the naive datetime to an aware datetime
        appointment_datetime = timezone.make_aware(appointment_datetime_naive, timezone.get_current_timezone())

        # Check if the appointment datetime is in the past
        if appointment_datetime <= timezone.now():
            return JsonResponse({'error': 'Cannot book an appointment in the past.'}, status=400)

        end_time = (appointment_datetime + timedelta(minutes=45)).time()

        appointment = Appointment.objects.create(
            patient=request.user,
            doctor=doctor,
            speciality=speciality,
            appointment_date=appointment_datetime.date(),
            start_time=appointment_datetime.time(),
            end_time=end_time
        )

        # Send email confirmation
        self.send_appointment_email(appointment)

        return JsonResponse({'message': 'Appointment booked successfully!'})

    def send_appointment_email(self, appointment):
        context = {
            'patient_name': f"{appointment.patient.first_name} {appointment.patient.last_name}",
            'doctor_name': f"{appointment.doctor.first_name} {appointment.doctor.last_name}",
            'speciality': appointment.speciality,
            'date': appointment.appointment_date.strftime("%b. %d, %Y"),
            'start_time': appointment.start_time.strftime("%I:%M %p"),
            'end_time': appointment.end_time.strftime("%I:%M %p"),
        }
        html_content = render_to_string('appointment_email.html', context)
        text_content = strip_tags(html_content)  # Fallback to plain text content

        # Create .ics file
        ics_file = create_ics_file(appointment)

        # Send the email with .ics attachment
        email = EmailMessage(
            'Appointment Confirmation',
            text_content,
            'manikantapadala358@gmail.com',  # From email
            [appointment.patient.email],  # To email
        )
        email.content_subtype = 'html'  # Set the primary content to be HTML
        email.attach('appointment.ics', ics_file.read(), 'text/calendar')
        email.send()

               
class AppointmentDetailView(LoginRequiredMixin, View):
    def get(self, request, pk):
        appointment = get_object_or_404(Appointment, pk=pk, patient=request.user)
        return render(request, 'appointment_details.html', {'appointment': appointment})

class DoctorAppointmentsView(LoginRequiredMixin, ListView):
    model = Appointment
    template_name = 'doctor_appointments.html'
    context_object_name = 'appointments'
    
    def get_queryset(self):
        return Appointment.objects.filter(doctor=self.request.user).order_by('appointment_date', 'start_time')
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        if user.is_authenticated:
            try:
                context['profile_picture_url'] = user.profile_picture.url
            except AttributeError:
                context['profile_picture_url'] = 'default-profile-pic-url.jpg'
        else:
            context['profile_picture_url'] = 'default-profile-pic-url.jpg'
        return context
    
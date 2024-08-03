from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login as auth_login, logout as auth_logout
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.views import View
from django.views.generic import ListView
from django.contrib.auth.hashers import make_password
from django.core.paginator import Paginator
from .models import User,BlogPost


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
                return JsonResponse({'redirect': f'/{user.user_type}_dashboard/'})
            else:
                return JsonResponse({'error_message': 'Invalid credentials.'})
        except User.DoesNotExist:
            return JsonResponse({'error_message': 'Username or Password are incorrect.'})

class DashboardView(LoginRequiredMixin,View):

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

class BlogListView(View):
    def get(self, request, category=None):
        sort_by = request.GET.get('sort', 'date')  # Default to sorting by date
        if category:
            posts = BlogPost.objects.filter(category=category, is_draft=False)
        else:
            posts = BlogPost.objects.filter(is_draft=False)

        search_query = request.GET.get('search', '')
        if search_query:
            posts = posts.filter(title__icontains=search_query) | posts.filter(author__username__icontains=search_query)

        if sort_by == 'likes':
            posts = posts.annotate(like_count=Count('likes')).order_by('-like_count')
        else:
            posts = posts.order_by('-created_at')

        paginator = Paginator(posts, 10)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)

        return render(request, 'blog_list.html', {'page_obj': page_obj, 'sort_by': sort_by})
    
class BlogDetailView(View):
    def get(self, request, pk):
        post = get_object_or_404(BlogPost, pk=pk, is_draft=False)
        return render(request, 'blog_detail.html', {'post': post})

class AddBlogPostView(View):
    def get(self, request):
        return render(request, 'add_blog_post.html', {'categories': BlogPost.CATEGORY_CHOICES})

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
        return redirect('doctor_dashboard')

class EditBlogPostView(View):
    def get(self, request, pk):
        post = get_object_or_404(BlogPost, pk=pk, author=request.user)
        return render(request, 'edit_blog_post.html', {'post': post, 'categories': BlogPost.CATEGORY_CHOICES})

    def post(self, request, pk):
        post = get_object_or_404(BlogPost, pk=pk, author=request.user)
        post.title = request.POST.get('title')
        post.image = request.FILES.get('image', post.image)
        post.category = request.POST.get('category')
        post.summary = request.POST.get('summary')
        post.content = request.POST.get('content')
        post.is_draft = request.POST.get('is_draft') == 'on'
        post.save()
        return redirect('doctor_dashboard')

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

    def get_queryset(self):
        return BlogPost.objects.filter(author=self.request.user, is_draft=True)  

class PostedBlogListView(LoginRequiredMixin, ListView):
    model = BlogPost
    template_name = 'posted_blog_list.html'
    context_object_name = 'blogs'

    def get_queryset(self):
        return BlogPost.objects.filter(author=self.request.user, is_draft=False)
from django.contrib import admin
from django.urls import path
from users.views import SignupView, LoginView, DashboardView, LogoutView
from users.views import BlogListView, BlogDetailView, AddBlogPostView, EditBlogPostView, LikeBlogPostView, DraftListView, PostedBlogListView
from django.conf.urls.static import static
from django.conf import settings

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', LoginView.as_view(), name='home'),
    path('login/', LoginView.as_view(), name='login'),
    path('signup/', SignupView.as_view(), name='signup'),
    path('patient_dashboard/', DashboardView.as_view(), name='patient_dashboard'),
    path('doctor_dashboard/', DashboardView.as_view(), name='doctor_dashboard'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('blogs/', BlogListView.as_view(), name='blog_list'),
    path('blogs/category/<str:category>/', BlogListView.as_view(), name='blog_list_category'),
    path('blogs/<int:pk>/', BlogDetailView.as_view(), name='blog_detail'),
    path('blogs/add/', AddBlogPostView.as_view(), name='add_blog_post'),
    path('blogs/edit/<int:pk>/', EditBlogPostView.as_view(), name='edit_blog_post'),
    path('blogs/like/<int:pk>/', LikeBlogPostView.as_view(), name='like_blog_post'),
    path('drafts/', DraftListView.as_view(), name='show_drafts'),
    path('posted_blogs/', PostedBlogListView.as_view(), name='show_posted_blogs'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

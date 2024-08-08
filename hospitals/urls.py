from django.contrib import admin
from django.urls import path
from users.views import SignupView, LoginView, DashboardView, LogoutView
from users.views import BlogListView, BlogDetailView, AddBlogPostView, EditBlogPostView, LikeBlogPostView, DraftListView, PostedBlogListView, DoctorListView, BookAppointmentView, AppointmentDetailView, DoctorAppointmentsView
from django.conf.urls.static import static
from django.conf import settings

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', DashboardView.as_view(), name='home'),
    path('login/', LoginView.as_view(), name='login'),
    path('signup/', SignupView.as_view(), name='signup'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('blogs/', BlogListView.as_view(), name='blog_list'),
    path('blogs/category/<str:category>/', BlogListView.as_view(), name='blog_list_category'),
    path('blogs/<int:pk>/', BlogDetailView.as_view(), name='blog_detail'),
    path('blogs/add/', AddBlogPostView.as_view(), name='add_blog_post'),
    path('blogs/edit/<int:pk>/', EditBlogPostView.as_view(), name='edit_blog_post'),
    path('blogs/like/<int:pk>/', LikeBlogPostView.as_view(), name='like_blog_post'),
    path('drafts/', DraftListView.as_view(), name='show_drafts'),
    path('posted_blogs/', PostedBlogListView.as_view(), name='show_posted_blogs'),
    path('doctors/',DoctorListView.as_view(),name='doctor_list'),
    path('doctors/<int:pk>/book/', BookAppointmentView.as_view(), name='book_appointment'),
    path('appointments/<int:pk>/', AppointmentDetailView.as_view(), name='appointment_details'),
     path('doctor/appointments/', DoctorAppointmentsView.as_view(), name='doctor_appointments'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
from django.contrib import admin
from django.urls import path
from users.views import SignupView, LoginView, DashboardView, LogoutView
from django.conf.urls.static import static
from django.conf import settings

urlpatterns = [
    path('admin/', admin.site.urls),
    path('',LoginView.as_view()),
    path('login/', LoginView.as_view(), name='login'),
    path('signup/', SignupView.as_view(), name='signup'),
    path('patient_dashboard/', DashboardView.as_view(), name='patient_dashboard'),
    path('doctor_dashboard/', DashboardView.as_view(), name='doctor_dashboard'),
    path('logout/', LogoutView.as_view(), name='logout'),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

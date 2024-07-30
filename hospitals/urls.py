"""
URL configuration for hospitals project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from users.views import signup, CustomLoginView,dashboard,logout
from django.conf.urls.static import static
from django.conf import settings
urlpatterns = [
    path('admin/', admin.site.urls),
    path('login/',CustomLoginView.as_view(),name='login'),
    path('signup/',signup,name='signup'),
    path('patient_dashboard/', dashboard, {'user_type': 'patient'}, name='patient_dashboard'),
    path('doctor_dashboard/', dashboard, {'user_type': 'doctor'}, name='doctor_dashboard'),
    path('logout/', logout, name='logout'),
]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

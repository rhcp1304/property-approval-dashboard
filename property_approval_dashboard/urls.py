from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views  # Import built-in auth views

urlpatterns = [
    path('admin/', admin.site.urls),

    # 1. AUTHENTICATION ROUTES
    # This points to the custom template you created: templates/registration/login.html
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),

    # Logout usually doesn't need a template; it just redirects based on settings.py
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),

    # 2. APP ROUTES
    path('', include('property.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
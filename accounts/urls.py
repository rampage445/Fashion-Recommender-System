from django.urls import path,include
from . import views
from django.conf.urls.static import static
from django.conf import settings
urlpatterns = [
    path('register/',views.reg,name='register'),
    path('login/',views.log,name='login'),
    path('logout/',views.logo,name='logout')
]

urlpatterns = urlpatterns + static(settings.MEDIA_URL,document_root=settings.MEDIA_ROOT)


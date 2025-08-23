"""rs URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/
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
from django.urls import path,include
from .views import home,shop,checkout,fav,wish,details,delete,search
from django.conf.urls.static import static
from django.conf import settings
urlpatterns = [
    path('',home,name="Home"),
    path("shop/<str:type>/",shop,name="shop"),
    path('shop/<str:type>/<str:category>/', shop, name='shopf'),
    path("checkout/",checkout,name='checkout'),
    path('fav/',fav,name='fav'),
    path('wish/',wish,name='wish'),
    path('details/<int:id>/',details,name='details'),
    path('del/',delete,name='del'),
    path('search/',search,name='search'),
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

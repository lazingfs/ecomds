
from django.contrib import admin
from django.urls import path, include
from  . import settings
from django.conf.urls.static import static
urlpatterns = [
    path('admin/', admin.site.urls),
    path ('', include('loja.urls')), 
    path ('loja/', include('loja.urls')),   
    
] 

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT) # Este é o mais importante para o CSS global
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

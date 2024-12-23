from django.contrib import admin
from django.urls import path, include

admin.site.site_header = ' '
admin.site.site_title = 'Admin Panel'
admin.site.index_title = 'Avenue'

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('system.urls')),
    path('accounts/', include('django.contrib.auth.urls')),
]

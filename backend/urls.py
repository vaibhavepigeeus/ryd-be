from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/users/', include('users.urls')),
    path('api/documents/', include('documents.urls')),
    path('api/filemanagement/', include('filemanagement.urls')),
    path('api/workflow/', include('workflow.urls')),
    path('api/audit/', include('audit.urls')),
    path('api/forms/', include('forms.urls')),
]

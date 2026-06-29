from django.urls import path
from .views import FileListAPIView, FileDownloadAPIView, update_archive, file_download, downloadFiles

urlpatterns = [
    path('files/', FileListAPIView.as_view(), name='file-list'),
    path('files/<int:file_id>/download/', FileDownloadAPIView.as_view(), name='file-download'),
    path('files/archive/', update_archive, name='file-archive'),
    path('files/download/', file_download, name='file-download'),
    path('download_files/', downloadFiles, name='download_files')
]

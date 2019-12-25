from django.urls import path
from django.conf.urls.static import static
from django.conf import settings
from . import views



urlpatterns = [
    path('', views.index, name = 'index'),
    path('find-vitem', views.find_vitem, name='find-vitem'),
    path('create-item', views.create_item, name='create-item'),
    path('create-item/agent', views.agent_form, name='create-agent'),
    path('scan-upload/<int:vitem_id>/', views.scan_upload, name='scan_upload'),
]

urlpatterns += static(settings.STATIC_URL, document_root = settings.STATIC_ROOT)
urlpatterns += static(settings.MEDIA_URL, document_root = settings.MEDIA_ROOT)
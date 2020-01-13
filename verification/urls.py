from django.urls import path
from django.conf.urls.static import static
from django.conf import settings
from . import views, form_views



urlpatterns = [
    path('', views.index, name = 'index'),
    path('find-vitem', views.find_vitem, name='find-vitem'),
    path('scan-upload/<int:vitem_id>/', form_views.scan_upload, name='scan_upload'),
    path('vitem/<int:vitem_id>/', form_views.vitem_form, name='vitem'),
    path('create-item', views.create_item, name='create-item'),
    path('create-item/agent', form_views.agent_form, name='create-agent'),
    path('create-item/agent/<int:agent_id>', form_views.agent_form, name='create-agent'),
    path('create-item/staff', form_views.staff_form, name='create-staff'),
    path('create-item/staff/<int:staff_id>', form_views.staff_form, name='create-staff'),
    
]

urlpatterns += static(settings.STATIC_URL, document_root = settings.STATIC_ROOT)
urlpatterns += static(settings.MEDIA_URL, document_root = settings.MEDIA_ROOT)
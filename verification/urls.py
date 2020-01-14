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
    path('create-item/agent/<int:obj_id>', form_views.agent_form, name='create-agent'),
    path('create-item/staff', form_views.staff_form, name='create-staff'),
    path('create-item/staff/<int:obj_id>', form_views.staff_form, name='create-staff'),
    path('create-item/partner', form_views.partner_form, name='create-partner'),
    path('create-item/partner/<int:obj_id>', form_views.partner_form, name='create-partner'),
    path('create-item/counterparty', form_views.counterparty_form, name='create-counterparty'),
    path('create-item/counterparty/<int:obj_id>', form_views.counterparty_form, name='create-counterparty'),
    
]

urlpatterns += static(settings.STATIC_URL, document_root = settings.STATIC_ROOT)
urlpatterns += static(settings.MEDIA_URL, document_root = settings.MEDIA_ROOT)
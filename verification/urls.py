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
    path('agent/new', form_views.agent_form, name='create-agent'),
    path('agent/<int:obj_id>', form_views.agent_form, name='detailing-agent'),
    path('staff/add', form_views.staff_form, name='create-staff'),
    path('staff/<int:obj_id>', form_views.staff_form, name='detailing-staff'),
    path('partner/add', form_views.partner_form, name='create-partner'),
    path('partner/<int:obj_id>', form_views.partner_form, name='detailing-partner'),
    path('counterparty/add', form_views.counterparty_form, name='create-counterparty'),
    path('counterparty/<int:obj_id>', form_views.counterparty_form, name='detailing-counterparty'),
    
]

urlpatterns += static(settings.STATIC_URL, document_root = settings.STATIC_ROOT)
urlpatterns += static(settings.MEDIA_URL, document_root = settings.MEDIA_ROOT)
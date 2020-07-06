from django.urls import path
from django.conf.urls.static import static
from django.conf import settings
from . import views, form_views, views_utils

urlpatterns = [
    path('', views.index, name = 'index'),
    path('sendmail', views.sendmail, name = 'sendmail'),
    path('find-vitem', views.vitem_list, name='find-vitem'),
    path('vitem-list/<str:param>', views.vitem_list, name='vitem-list'),
    path('scan/upload/', views.scan_upload, name='scan-upload'),
    path('scan/delete/<int:scan_id>/', views.scan_delete, name='scan-delete'),
    path('vitem/<int:vitem_id>/', form_views.vitem_form, name='vitem'),
    path('create-item', views.create_item, name='create-item'),
    path('item-selection', views.new_item_type_selection, name='item-selection'),
    path('item-searcher/<str:item_type>&<int:owr_id>', views.item_searcher, name='item-searcher'),
    path('short-item/add', form_views.short_item_form, name='create-short-item'),
    path('short-item/<int:obj_id>', form_views.short_item_form, name='detailing-short-item'),
    path('agent/add', form_views.agent_form, name='create-agent'),
    path('agent/<int:obj_id>', form_views.agent_form, name='detailing-agent'),
    path('staff/add', form_views.staff_form, name='create-staff'),
    path('staff/<int:obj_id>', form_views.staff_form, name='detailing-staff'),
    path('partner/add', form_views.partner_form, name='create-partner'),
    path('partner/<int:obj_id>', form_views.partner_form, name='detailing-partner'),
    path('counterparty/add', form_views.counterparty_form, name='create-counterparty'),
    path('counterparty/<int:obj_id>', form_views.counterparty_form, name='detailing-counterparty'),
    path('owr/<int:owr_id>/ceo/add', form_views.ceo_form, name='create-ceo'),
    path('owr/<int:owr_id>/ceo/<int:pwr_id>', form_views.ceo_form, name='detailing-ceo'),
    path('owr/<int:owr_id>/ben/add', form_views.ben_form, name='create-ben'),
    path('owr/<int:owr_id>/ben/<int:pwr_id>', form_views.ben_form, name='detailing-ben'),
]

urlpatterns += static(settings.STATIC_URL, document_root = settings.STATIC_ROOT)
urlpatterns += static(settings.MEDIA_URL, document_root = settings.MEDIA_ROOT)
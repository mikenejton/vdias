from django.contrib import admin
from django.apps import apps
from .models import ExtendedUser
from . import models
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin
from django.contrib.sessions.models import Session

class SessionAdmin(admin.ModelAdmin):
    def _session_data(self, obj):
        return obj.get_decoded()
    list_display = ['session_key', '_session_data', 'expire_date']
admin.site.register(Session, SessionAdmin)


def auto_register(model, ldl):
    #Get all fields from model, but exclude autocreated reverse relations
    field_list = [f.name for f in model._meta.get_fields() if f.auto_created == False]
    field_list.insert(0, 'id')
    # Dynamically create ModelAdmin class and register it.
    my_admin = type('MyAdmin', (admin.ModelAdmin,), 
                        {'list_display':field_list, 
                        'list_display_links': ldl,
                        'list_filter': [x for x in ldl if x != 'id'] if ldl else [],
                        }
                    )
    try:
        admin.site.register(model,my_admin)
    except:
        # This model is already registered
        pass

class ProfileInline(admin.StackedInline):
    model = ExtendedUser
    can_delete = False
    verbose_name_plural = 'Extended'
    fk_name = 'user'

class CustomUserAdmin(UserAdmin):
    inlines = (ProfileInline, )

    def get_inline_instances(self, request, obj=None):
        if not obj:
            return list()
        return super(CustomUserAdmin, self).get_inline_instances(request, obj)


admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)    

model_admin_links={
    'datalogger': ['id', 'model_name'],
    'userrole': ['id', 'role_name'],
    'organization': ['id', 'org_form', 'org_name'],
    'verificationitem': ['id', 'person', 'organization'],
    'vitemchat': ['id', 'vitem'],
    'organizationwithrole': ['id', 'organization'],
    'personwithrole': ['id', 'person'],
    'docstorage': ['id', 'model_name', 'doc_type'],
    'person': ['id', 'fio']

}
for model in apps.get_app_config('verification').get_models():
    if model != ExtendedUser:
        if model._meta.model_name in model_admin_links:
            auto_register(model, model_admin_links[model._meta.model_name])
        else:
            auto_register(model, None)
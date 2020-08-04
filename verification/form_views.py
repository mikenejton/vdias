from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.urls import reverse

from . import models
from . import forms
from . import views_utils
from . import views_sub_func


# формы физ.лиц
@login_required
def agent_form(request, obj_id=None):
    result = views_sub_func.pwr_call(request, obj_id, None, 'Агент', request.user.extendeduser.user_role.role_name)
    return result

@login_required
def staff_form(request, obj_id=None):
    result = views_sub_func.pwr_call(request, obj_id, None, 'Сотрудник', 'Сотрудники')
    return result

@login_required
def ceo_form(request, owr_id=None, obj_id=None):
    result = views_sub_func.pwr_call(request, obj_id, owr_id, 'Ген. директор', None)
    return result

@login_required
def ben_form(request, owr_id=None, obj_id=None):
    result = views_sub_func.pwr_call(request, obj_id, owr_id, 'Бенефициар', None)
    return result
# --------------------------------------------------------------

# формы организаций
@login_required
def partner_form(request, obj_id=None):
    result = views_sub_func.owr_call(request, obj_id, 'Создание партнера', 'Партнер')
    return result

@login_required
def counterparty_form(request, obj_id=None):
    result = views_sub_func.owr_call(request, obj_id, 'Создание контрагента', 'Контрагент')
    return result
# --------------------------------------------------------------

# формы короткой заявки (с id и ссылкой на Еву)
def short_item_form(request, obj_id=None):
    result = views_sub_func.short_item_call(request, obj_id)
    return result

# --------------------------------------------------------------

# VITEM MAIN FORM
@login_required
def vitem_form(request, vitem_id=None):
    context = views_utils.get_base_context(request.user)
    context['statuses'] = models.DiasStatus.objects.all()
    if views_utils.accessing(vitem_id, 'VerificationItem', request.user):
        if vitem_id:
            vitem_qs = models.VerificationItem.objects.filter(id=vitem_id)
            if len(vitem_qs):
                vitem = vitem_qs[0]
                if request.method == 'GET':
                    context['vitem'] = vitem
                    context['page_title'] = f'Заявка № {vitem.id}'
                    msgs = models.VitemChat.objects.filter(vitem = vitem).order_by('-created')
                    context['msgs'] = msgs
                    if vitem.person:
                        context['pwr'] = vitem.person
                        # context['roles'] = models.PersonWithRole.objects.filter(person__id = context['pwr'].person.id).exclude(id = context['pwr'].id)
                        context['roles'] = models.PersonWithRole.objects.filter(person__id = context['pwr'].person.id)
                        # scan_list = models.DocStorage.objects.filter(model_id = vitem.person.person.id, model_name = 'Person')
                        form_template = 'verification/forms/objects/vitem_agent_form.html'
                        context['edit_link'] = [{'Агент': 'detailing-agent', 'Сотрудник': 'detailing-staff', 'Ген. директор': 'detailing-ceo', 'Бенефициар': 'detailing-ben'}[vitem.person.role.role_name], vitem.person.id]
                        if context['pwr'].role.role_name in ['Ген. директор', 'Бенефициар']:
                            owr_qs = models.OrganizationWithRole.objects.filter(organization__id = context['pwr'].related_organization.id)
                            if len(owr_qs):
                                context['owr_id'] = owr_qs[0].id

                    elif vitem.organization:
                        context['owr'] = vitem.organization
                        context['roles'] = models.OrganizationWithRole.objects.filter(organization__id = context['owr'].organization.id).exclude(id = context['owr'].id)
                        # scan_list = models.DocStorage.objects.filter(model_id = vitem.organization.organization.id, model_name = 'Organization')
                        form_template = 'verification/forms/objects/vitem_organization_form.html'
                        context['edit_link'] = ['detailing-partner' if vitem.organization.role.role_name == 'Партнер' else 'detailing-counterparty', vitem.organization.id]
                        context['bens'] = models.PersonWithRole.objects.filter(related_organization__id = context['owr'].organization.id, role__role_name = 'Бенефициар')
                        context['ceo'] = models.PersonWithRole.objects.filter(related_organization__id = context['owr'].organization.id, role__role_name = 'Ген. директор')
                    elif vitem.short_item:
                        context['short_item'] = vitem.short_item
                        # scan_list = models.DocStorage.objects.filter(model_name = 'ShortItem')
                        context['edit_link'] = ['detailing-short-item', vitem.short_item.id]
                        form_template = 'verification/forms/objects/vitem_short_item_form.html'

                    # context['scan_list'] = scan_list.filter(to_del = False)
                    
                    # if request.user.extendeduser.user_role.role_lvl <= 3:
                    #     context['deleted_scan_list'] = scan_list.filter(to_del = True)
                    context['form'] = forms.VerificationItemForm(instance=vitem)
                    return render(request, form_template, context)
                else:
                    if 'btn_save' in request.POST:
                        ff = forms.VerificationItemForm(request.POST)
                        if ff.is_valid():
                            for key in ff.fields:
                                if key in request.POST:
                                    if hasattr(vitem, key):
                                        if getattr(vitem, key) != ff.cleaned_data[key]:
                                            setattr(vitem, key, ff.cleaned_data[key])
                            views_utils.update_logger('VerificationItem', vitem.id, 'Обновление записи', request.user.extendeduser, vitem)
                        vitem.save()
                        
                        for vitem_object in ['person', 'organization', 'short_item']:
                            if getattr(vitem, vitem_object):
                                verificated = 'одобрено' in vitem.status.status.lower()
                                if getattr(getattr(vitem, vitem_object), 'verificated') != verificated:
                                   setattr(getattr(vitem, vitem_object), 'verificated', verificated)
                                   getattr(vitem, vitem_object).save()
                                break
                        
                        redirect(reverse('vitem', args=[vitem_id]))
                    elif 'btn_to_fix' in request.POST:
                        vitem.to_fix = True
                        vitem.fixed = False
                        vitem.status = models.DiasStatus.objects.get(id=3)
                        views_utils.update_logger('VerificationItem', vitem.id, 'Обновление записи', request.user.extendeduser, vitem)
                        vitem.save()
                        views_utils.newChatMessage(vitem, '{}: {}'.format('На доработку', request.POST['fix_comment']), request.user.extendeduser)
                    elif 'btn_fixed' in request.POST:
                        vitem.to_fix = False
                        vitem.fixed = True
                        vitem.status = models.DiasStatus.objects.get(id=4)
                        views_utils.update_logger('VerificationItem', vitem.id, 'Обновление записи', request.user.extendeduser, vitem)
                        vitem.save()
                        views_utils.newChatMessage(vitem, '{}: {}'.format('Доработано', request.POST['fix_comment']), request.user.extendeduser)
                    elif 'btn_take_to' in request.POST:
                        vitem.case_officer = request.user.extendeduser
                        vitem.status = models.DiasStatus.objects.get(id=2)
                        views_utils.update_logger('VerificationItem', vitem.id, 'Обновление записи', request.user.extendeduser, vitem)
                        vitem.save()
                    elif 'btn_add_comment' in request.POST and len(request.POST['chat_message']) > 0:                    
                        views_utils.newChatMessage(vitem, request.POST['chat_message'], request.user.extendeduser)


                    return redirect(reverse('vitem', args=[vitem_id]))
    else:
        context['err_txt'] = 'Запрашиваемая страница не существует или у Вас недостаточно прав на ее просмотр'
        return render(request, 'verification/404.html', context)
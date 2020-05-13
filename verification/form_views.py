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
    result = views_sub_func.pwr_call(request, obj_id, None, 'Штатный сотрудник', 'Штатные сотрудники')
    return result

@login_required
def ceo_form(request, owr_id=None, pwr_id=None):
    result = views_sub_func.pwr_call(request, pwr_id, owr_id, 'Ген. директор', None)
    return result

@login_required
def ben_form(request, owr_id=None, pwr_id=None):
    result = views_sub_func.pwr_call(request, pwr_id, owr_id, 'Бенефициар', None)
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
                        scan_list = models.DocStorage.objects.filter(model_id = vitem.person.person.id, model_name = 'Person')
                        form_template = 'verification/forms/objects/vitem_agent_form.html'
                        context['edit_link'] = ['detailing-agent' if vitem.person.role == 'Агент' else 'detailing-staff', vitem.person.id]
                    elif vitem.organization:
                        context['owr'] = vitem.organization
                        scan_list = models.DocStorage.objects.filter(model_id = vitem.organization.organization.id, model_name = 'Organization')
                        form_template = 'verification/forms/objects/vitem_organization_form.html'
                        context['edit_link'] = ['detailing-partner' if vitem.organization.role == 'Партнер' else 'detailing-counterparty', vitem.organization.id]
                        context['bens'] = models.PersonWithRole.objects.filter(related_organization__id = context['owr'].id, role = 'Бенефициар')
                        context['ceo'] = models.PersonWithRole.objects.filter(related_organization__id = context['owr'].id, role = 'Ген. директор')
                    elif vitem.short_item:
                        context['short_item'] = vitem.short_item
                        scan_list = models.DocStorage.objects.filter(model_name = 'ShortItem')
                        context['edit_link'] = ['detailing-short-item', vitem.short_item.id]
                        form_template = 'verification/forms/objects/vitem_short_item_form.html'

                    context['scan_list'] = scan_list.filter(to_del = False)
                    
                    if request.user.extendeduser.user_role.role_lvl <= 3:
                        context['deleted_scan_list'] = scan_list.filter(to_del = True)
                    context['form'] = forms.VerificationItemForm(instance=vitem)
                    return render(request, form_template, context)
                else:
                    if 'btn_save' in request.POST:
                        ff = forms.VerificationItemForm(request.POST)
                        if 'dias_status' not in request.POST:
                            ff.dias_status = vitem.dias_status
                        if ff.is_valid():
                            for key in ff.fields:
                                if hasattr(vitem, key):
                                    if getattr(vitem, key) != ff.cleaned_data[key]:
                                        setattr(vitem, key, ff.cleaned_data[key])
                            views_utils.update_logger('VerificationItem', vitem.id, 'Обновление записи', request.user.extendeduser, vitem)
                        vitem.save()
                        
                        return redirect('index')
                    elif 'btn_to_fix' in request.POST:
                        vitem.to_fix = True
                        vitem.fixed = False
                        vitem.dias_status = 'На доработке'
                        views_utils.update_logger('VerificationItem', vitem.id, 'Обновление записи', request.user.extendeduser, vitem)
                        vitem.save()
                        views_utils.newChatMessage(vitem, '{}: {}'.format('На доработку', request.POST['fix_comment']), request.user.extendeduser)
                    elif 'btn_fixed' in request.POST:
                        vitem.to_fix = False
                        vitem.fixed = True
                        vitem.dias_status = 'Доработано'
                        views_utils.update_logger('VerificationItem', vitem.id, 'Обновление записи', request.user.extendeduser, vitem)
                        vitem.save()
                        views_utils.newChatMessage(vitem, '{}: {}'.format('Доработано', request.POST['fix_comment']), request.user.extendeduser)
                    elif 'btn_take_to' in request.POST:
                        vitem.case_officer = request.user.extendeduser
                        vitem.dias_status = 'В работе'
                        views_utils.update_logger('VerificationItem', vitem.id, 'Обновление записи', request.user.extendeduser, vitem)
                        vitem.save()
                    elif 'btn_add_comment' in request.POST and len(request.POST['chat_message']) > 0:                    
                        views_utils.newChatMessage(vitem, request.POST['chat_message'], request.user.extendeduser)


                    return redirect(reverse('vitem', args=[vitem_id]))
    else:
        context['err_txt'] = 'Запрашиваемая страница не существует или у Вас недостаточно прав на ее просмотр'
        return render(request, 'verification/404.html', context)
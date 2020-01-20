from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.urls import reverse

from . import models
from . import forms
from . import utils
from . import objects_view

def newChatMessage(vitem, message, author):
    new_msg = models.VitemChat()
    new_msg.vitem = vitem
    new_msg.msg = message
    new_msg.author = author
    new_msg.save()
    utils.update_logger('VitemChat', new_msg.id, '', author)

@login_required
def agent_form(request, obj_id=None):
    
    result = objects_view.pwr_call(request, obj_id, None, 'Агент', request.user.extendeduser.user_role.role_name)
    return result

@login_required
def staff_form(request, obj_id=None):
    
    result = objects_view.pwr_call(request, obj_id, None, 'Штатный сотрудник', 'Штатные сотрудники')
    return result

@login_required
def ceo_form(request, owr_id=None, pwr_id=None):
    
    result = objects_view.pwr_call(request, pwr_id, owr_id, 'Ген. директор', None)
    return result

@login_required
def ben_form(request, owr_id=None, pwr_id=None):
    
    result = objects_view.pwr_call(request, pwr_id, owr_id, 'Бенефициар', None)
    return result


def person_form(request, obj_id, create_title, update_title, organization_query_role):
    context = utils.get_base_context(request.user)
    context['doc_types'] = ['Паспорт 1 страница', 'Паспорт 2 страница', 'Анкета', 'Иной документ']
    person_organization = models.OrganizationWithRole.objects.all()
    if request.method == 'POST':
        if 'id' in request.POST:
            form = forms.PersonForm(data=request.POST, instance=models.Person.objects.get(id=request.POST['id']))
        else:
            form = forms.PersonForm(data=request.POST)
        if form.is_valid():
            if 'id' in request.POST:
                created_person = form.save(commit=False)
                utils.update_logger('Person', created_person.id, 'Обновление записи', request.user.extendeduser, created_person)
                person_wr = models.PersonWithRole.objects.get(person_id = request.POST['id'])
                if person_wr.related_organization.id != request.POST['related_organization']:
                    person_wr.related_organization = models.OrganizationWithRole.objects.get(id = request.POST['related_organization'])
                    person_wr.save()
                created_person.save()
                
                return redirect(reverse('detailing-agent', args=[person_wr.id]))
            else:
                created_person = form.save()
                utils.update_logger('Person', created_person.id, '', request.user.extendeduser)
                new_person_wr = models.PersonWithRole()
                new_person_wr.person = created_person
                new_person_wr.person_role = update_title
                new_person_wr.author = request.user.extendeduser
                if 'related_organization' in request.POST:
                    new_person_wr.related_organization = models.OrganizationWithRole.objects.get(id = request.POST['related_organization'])
                new_person_wr.save()
                utils.update_logger('PersonWithRole', new_person_wr.id, '', request.user.extendeduser)
                vi = models.VerificationItem()
                vi.person = new_person_wr
                vi.dias_status = ''
                vi.author = request.user.extendeduser
                vi.save()
                utils.update_logger('VerificationItem', vi.id, '', request.user.extendeduser)
                return redirect(reverse('detailing-agent', args=[new_person_wr.id]))
    else:
        if obj_id:
            person_wr = models.PersonWithRole.objects.filter(id = obj_id)
            person_organization = person_organization.filter(id = person_wr[0].related_organization.id)
            context['scan_list'] = models.DocStorage.objects.filter(model_id = obj_id, model_name = 'PersonWithRole', to_del = False)
            context['vitem_id'] = models.VerificationItem.objects.filter(person__id = obj_id)[0].id
            context['vitem_is_filled'] = models.VerificationItem.objects.filter(person__id = obj_id)[0].is_filled
            if request.user.extendeduser.user_role.role_lvl <= 3:
                context['deleted_scan_list'] = models.DocStorage.objects.filter(model_id = obj_id, model_name = 'PersonWithRole', to_del = True)
            if len(person_wr) > 0:
                person = person_wr[0].person
                form = forms.PersonForm(instance=person)
                context['page_title'] = update_title
                context['person_wr'] = person_wr[0]
                context['object_title'] = f"{context['person_wr'].person.fio}"
            else:
                return render(request, 'verification/404.html', context)
        else:
            if request.user.extendeduser.user_role == 'HR':
                person_organization = person_organization.filter(organization_role = 'Штатные сотрудники')
            elif request.user.extendeduser.user_role.role_lvl > 3:
                person_organization = person_organization.filter(organization_role = organization_query_role)
            
            form = forms.PersonForm()
            context['page_title'] = create_title
    context['form'] = form
    if request.user.extendeduser.user_role == 'HR':
        person_organization = person_organization.filter(organization_role = 'Штатные сотрудники')
    elif request.user.extendeduser.user_role.role_lvl > 3:
        person_organization = person_organization.filter(organization_role = organization_query_role)
    context['org_list'] = person_organization
    return render(request, 'verification/forms/common/person_form_common.html', context)

#------------------------------------------------------------------------------------------

@login_required
def partner_form(request, obj_id=None):
    result = organization_form(request, obj_id, 'Создание партнера', 'Партнер')
    return result

@login_required
def counterparty_form(request, obj_id=None):
    result = organization_form(request, obj_id, 'Создание контрагента', 'Контрагент')
    return result

def organization_form(request, obj_id, create_title, update_title):
    context = utils.get_base_context(request.user)
    context['vitem_id'] = models.VerificationItem.objects.filter(organization__id = obj_id)[0].id
    context['doc_types'] = ['Скан анкеты', 'Скан устава', 'Скан свидетельства о гос.рег.', 'Скан свидетельства о постановке на налоговый учет', 'Иной документ']
    if request.method == 'GET':
        if obj_id:
            owr = models.OrganizationWithRole.objects.filter(id = obj_id)
            if len(owr) > 0:
                organization = owr[0].organization
                form = forms.OrganizationForm(instance=organization)
                context['page_title'] = update_title
                context['owr'] = owr[0]
                context['object_title'] = f"{context['owr'].organization.full_name} ({context['page_title']})"
                context['ceo'] = models.PersonWithRole.objects.filter(related_organization__id = owr[0].id, person_role = 'Ген. директор')[0]
                context['bens'] = models.PersonWithRole.objects.filter(related_organization__id = owr[0].id, person_role = 'Бенефициар')
                context['scan_list'] = models.DocStorage.objects.filter(model_id = owr[0].organization.id, model_name = 'Organization', to_del = False)
                if request.user.extendeduser.user_role.role_lvl <= 3:
                    context['deleted_scan_list'] = models.DocStorage.objects.filter(model_id = owr[0].organization.id, model_name = 'Organization', to_del = True)
            else:
                return render(request, 'verification/404.html', context)
        else:
            form = forms.OrganizationForm()
            context['page_title'] = create_title
        context['form'] = form
        return render(request, 'verification/forms/common/organization_form_common.html', context)
    else:
        pass

# VITEM MAIN FORM
@login_required
def vitem_form(request, vitem_id=None):
    context = utils.get_base_context(request.user)
    if vitem_id:
        vitem_qs = models.VerificationItem.objects.filter(id=vitem_id)
        if len(vitem_qs):
            vitem = vitem_qs[0]
            if request.user.extendeduser.user_role.role_lvl <= 3 or vitem.author.user_role == request.user.extendeduser.user_role:
                if request.method == 'GET':
                    context['vitem'] = vitem
                    context['page_title'] = f'Заявка № {vitem.id}'
                    msgs = models.VitemChat.objects.filter(vitem = vitem).order_by('-created')
                    context['msgs'] = msgs
                    if vitem.person:
                        context['person'] = vitem.person
                        scan_list = models.DocStorage.objects.filter(model_id = vitem.person.id, model_name = 'PersonWithRole')
                        form_template = 'verification/forms/objects/vitem_agent_form.html'
                        context['edit_link'] = ['detailing-agent' if vitem.person.person_role == 'Агент' else 'detailing-staff', vitem.person.id]
                    else:
                        context['organization'] = vitem.organization
                        scan_list = models.DocStorage.objects.filter(model_id = vitem.organization.id, model_name = 'OrganizationWithRole')
                        form_template = 'verification/forms/objects/vitem_organization_form.html'
                        context['edit_link'] = ['detailing-partner' if vitem.organization.organization_role == 'Партнер' else 'detailing-counterparty', vitem.organization.id]
                    context['scan_list'] = scan_list.filter(to_del = False)
                    if request.user.extendeduser.user_role.role_lvl <= 3:
                        context['deleted_scan_list'] = scan_list.filter(to_del = True)
                    context['form'] = forms.VerificationItemForm(instance=vitem)
                    return render(request, form_template, context)
                else:
                    if 'btn_save' in request.POST:
                        ff = forms.VerificationItemForm(request.POST)
                        if ff.is_valid():
                            for key in ff.fields:
                                if hasattr(vitem, key):
                                    if getattr(vitem, key) != ff.cleaned_data[key]:
                                        setattr(vitem, key, ff.cleaned_data[key])
                            utils.update_logger('VerificationItem', vitem.id, 'Обновление записи', request.user.extendeduser, vitem)
                        vitem.save()
                        return redirect('index')
                    elif 'btn_to_fix' in request.POST:
                        vitem.to_fix = True
                        vitem.fixed = False
                        vitem.dias_status = 'На доработке'
                        utils.update_logger('VerificationItem', vitem.id, 'Обновление записи', request.user.extendeduser, vitem)
                        vitem.save()
                        newChatMessage(vitem, '{}: {}'.format('На доработку', request.POST['fix_comment']), request.user.extendeduser)
                    elif 'btn_fixed' in request.POST:
                        vitem.to_fix = False
                        vitem.fixed = True
                        vitem.dias_status = 'Доработано'
                        utils.update_logger('VerificationItem', vitem.id, 'Обновление записи', request.user.extendeduser, vitem)
                        vitem.save()
                        newChatMessage(vitem, '{}: {}'.format('Доработано', request.POST['fix_comment']), request.user.extendeduser)
                    elif 'btn_take_to' in request.POST:
                        vitem.case_officer = request.user.extendeduser
                        vitem.dias_status = 'В работе'
                        utils.update_logger('VerificationItem', vitem.id, 'Обновление записи', request.user.extendeduser, vitem)
                        vitem.save()
                    elif 'btn_add_comment' in request.POST and len(request.POST['chat_message']) > 0:                    
                        newChatMessage(vitem, request.POST['chat_message'], request.user.extendeduser)

                    return redirect(reverse('vitem', args=[vitem_id]))
            else:
                context['err_txt'] = 'У вас недостаточно прав на просмотр данной страницы'
    
    return render(request, 'verification/404.html', context)
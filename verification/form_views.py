from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.urls import reverse

from . import models
from . import forms
from . import utils

def newChatMessage(vitem, message, author):
    new_msg = models.VitemChat()
    new_msg.vitem = vitem
    new_msg.msg = message
    new_msg.author = author
    new_msg.save()
    utils.update_logger('VitemChat', new_msg.id, '', author)

@login_required
def agent_form(request, obj_id=None):
    context = utils.get_base_context(request.user)
    context['doc_types'] = ['Паспорт 1 страница', 'Паспорт 2 страница', 'Анкета', 'Иной документ']
    if request.user.extendeduser.user_role.role_lvl < 3: # уровень роли сотрудников АиС и Админа - 2 и 1 соответственно
        agent_organization = models.OrganizationWithRole.objects.all()
    else:
        agent_organization = models.OrganizationWithRole.objects.filter(organization_role = request.user.extendeduser.user_role.role_name)
    context['org_list'] = agent_organization
    if request.method == 'POST':
        if 'id' in request.POST:
            form = forms.PersonForm(data=request.POST, instance=models.Person.objects.get(id=request.POST['id']))
        else:
            form = forms.PersonForm(data=request.POST)
        if form.is_valid():
            if 'id' in request.POST:
                created_person = form.save(commit=False)
                utils.update_logger('Person', created_person.id, 'Обновление записи', request.user.extendeduser, created_person)
                agent_role = models.PersonWithRole.objects.get(person_id = request.POST['id'])
                if agent_role.related_organization.id != request.POST['related_organization']:
                    agent_role.related_organization = models.OrganizationWithRole.objects.get(id = request.POST['related_organization'])
                    agent_role.save()
                created_person.save()
                vi = models.VerificationItem.objects.get(person__id=agent_role.id)
                return redirect(reverse('vitem', args=[vi.id]))
            else:
                created_person = form.save()
                utils.update_logger('Person', created_person.id, '', request.user.extendeduser)
                agent_role = models.PersonWithRole()
                agent_role.person = created_person
                agent_role.person_role = 'Агент'
                agent_role.author = request.user.extendeduser
                if 'related_organization' in request.POST:
                    agent_role.related_organization = models.OrganizationWithRole.objects.get(id = request.POST['related_organization'])
                agent_role.save()
                utils.update_logger('PersonWithRole', agent_role.id, '', request.user.extendeduser)
                vi = models.VerificationItem()
                vi.person = agent_role
                vi.dias_status = 'Новая'
                vi.author = request.user.extendeduser
                vi.save()
                utils.update_logger('VerificationItem', vi.id, '', request.user.extendeduser)
                return redirect(reverse('vitem', args=[vi.id]))
    else:
        if obj_id:
            person_wr = models.PersonWithRole.objects.filter(id = obj_id)
            context['scan_list'] = models.DocStorage.objects.filter(model_id = obj_id, model_name = 'PersonWithRole', to_del = False)
            if request.user.extendeduser.user_role.role_lvl <= 3:
                context['deleted_scan_list'] = models.DocStorage.objects.filter(model_id = obj_id, model_name = 'PersonWithRole', to_del = True)
            if len(person_wr) > 0:
                person = person_wr[0].person
                form = forms.PersonForm(instance=person)
                context['page_title'] = 'Агент'
                context['person_wr'] = person_wr[0]
            else:
                return render(request, 'verification/404.html')
        else:
            form = forms.PersonForm()
            context['page_title'] = 'Новый агент'
    context['form'] = form
    return render(request, 'verification/forms/objects/person_form.html', context)

@login_required
def staff_form(request, obj_id=None):
    context = utils.get_base_context(request.user)
    context['doc_types'] = ['Паспорт 1 страница', 'Паспорт 2 страница', 'Анкета', 'Иной документ']
    if request.user.extendeduser.user_role == 'HR' or request.user.extendeduser.user_role.role_lvl < 3:
        staff_organization = models.OrganizationWithRole.objects.filter(organization_role = 'Штатные сотрудники')
        context['org_list'] = staff_organization
    else:
        return render(request, 'verification/404.html', {'err_txt': 'У вас недостаточно прав на создание заявки'})
    if request.method == 'POST':
        if 'id' in request.POST:
            form = forms.PersonForm(data=request.POST, instance=models.Person.objects.get(id=request.POST['id']))
        else:
            form = forms.PersonForm(data=request.POST)
        
        if form.is_valid():
            if 'id' in request.POST:
                created_person = form.save(commit=False)
                utils.update_logger('Person', created_person.id, 'Обновление записи', request.user.extendeduser, created_person)
                staff_role = models.PersonWithRole.objects.get(person_id = request.POST['id'])
                if staff_role.related_organization.id != request.POST['related_organization']:
                    staff_role.related_organization = models.OrganizationWithRole.objects.get(id = request.POST['related_organization'])
                    staff_role.save()
                created_person.save()
                vi = models.VerificationItem.objects.get(person__id=staff_role.id)
                return redirect(reverse('vitem', args=[vi.id]))
            else:
                created_person = form.save()
                utils.update_logger('Person', created_person.id, '', request.user.extendeduser)
                staff_role = models.PersonWithRole()
                staff_role.person = created_person
                staff_role.person_role = 'Штатный сотрудник'
                staff_role.author = request.user.extendeduser
                if 'related_organization' in request.POST:
                    staff_role.related_organization = models.OrganizationWithRole.objects.get(id = request.POST['related_organization'])
                staff_role.save()
                utils.update_logger('PersonWithRole', staff_role.id, '', request.user.extendeduser)
                vi = models.VerificationItem()
                vi.person = staff_role
                vi.dias_status = ''
                vi.author = request.user.extendeduser
                vi.save()
                utils.update_logger('VerificationItem', vi.id, '', request.user.extendeduser)
                return redirect(reverse('vitem', args=[vi.id]))
    else:
        if obj_id:
            person_wr = models.PersonWithRole.objects.filter(id = obj_id)
            context['scan_list'] = models.DocStorage.objects.filter(model_id = obj_id, model_name = 'PersonWithRole', to_del = False)
            if request.user.extendeduser.user_role.role_lvl <= 3:
                context['deleted_scan_list'] = models.DocStorage.objects.filter(model_id = obj_id, model_name = 'PersonWithRole', to_del = True)
            if len(person_wr) > 0:
                person = person_wr[0].person
                form = forms.PersonForm(instance=person)
                context['page_title'] = 'Штатный сотрудник'
                context['person_wr'] = person_wr[0]
            else:
                return render(request, 'verification/404.html')
        else:
            form = forms.PersonForm()
            context['page_title'] = 'Создание штатного сотрудника'
    context['form'] = form
    return render(request, 'verification/forms/objects/person_form.html', context)

@login_required
def partner_form(request, obj_id=None):
    result = organization_form(request, obj_id, 'Создание партнера', 'Партнер')
    return render(result[0], result[1], result[2])

@login_required
def counterparty_form(request, obj_id=None):
    result = organization_form(request, obj_id, 'Создание контрагента', 'Контрагент')
    return render(result[0], result[1], result[2])

def organization_form(request, obj_id, create_title, update_title):
    context = utils.get_base_context(request.user)
    if request.method == 'GET':
        if obj_id:
            organization_wr = models.OrganizationWithRole.objects.filter(id = obj_id)
            if len(organization_wr) > 0:
                organization = organization_wr[0].organization
                form = forms.OrganizationForm(instance=organization)
                context['page_title'] = update_title
                context['organization_wr'] = organization_wr[0]
            else:
                return [request, 'verification/404.html', context]
        else:
            form = forms.PersonForm()
            context['page_title'] = create_title
            context['form'] = form
        return [request, 'verification/forms/objects/organization_form.html', context]
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
                        form_template = 'verification/forms/objects/vitem_agent.html'
                        context['edit_link'] = ['detailing-agent' if vitem.person.person_role == 'Агент' else 'detailing-staff', vitem.person.id]
                    else:
                        context['organization'] = vitem.organization
                        scan_list = models.DocStorage.objects.filter(model_id = vitem.organization.id, model_name = 'OrganizationWithRole')
                        form_template = 'verification/forms/objects/vitem_organization.html'
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
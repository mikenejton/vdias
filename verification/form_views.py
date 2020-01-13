import os
from datetime import datetime
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.core.files.storage import default_storage
from django.conf import settings
from django.urls import reverse

from . import models
from . import forms

@login_required
def vitem_form(request, vitem_id=None):
    context = {}
    if vitem_id:
        vitem_qs = models.VerificationItem.objects.filter(id=vitem_id)
        if len(vitem_qs):
            vitem = vitem_qs[0]
            if request.user.extendeduser.user_role.role_lvl <= 3 or vitem.author.user_role == request.user.extendeduser.user_role:
                if request.method == 'GET':
                    context['vitem'] = vitem
                    context['page_title'] = 'Заявка'
                    msgs = models.VitemChat.objects.filter(vitem = vitem).order_by('-created')
                    context['msgs'] = msgs
                    if vitem.person:
                        context['person'] = vitem.person
                        scan_q = models.DocStorage.objects.filter(model_id = vitem.person.id, model_name = 'PersonWithRole')
                        form_template = 'verification/forms/objects/vitem_agent.html'
                    else:
                        context['organization'] = vitem.organization
                        scan_q = models.DocStorage.objects.filter(model_id = vitem.organization.id, model_name = 'OrganizationWithRole')
                        form_template = 'verification/forms/objects/vitem_organization.html'
                    context['scan_q'] = scan_q
                    context['form'] = forms.VerificationItemForm(instance=vitem)
                    return render(request, form_template, context)
                else:
                    print(request.POST)
                    if 'btn_save' in request.POST:
                        ff = forms.VerificationItemForm(request.POST)
                        if ff.is_valid():
                            for key in ff.fields:
                                if hasattr(vitem, key):
                                    if getattr(vitem, key) != ff.cleaned_data[key]:
                                        setattr(vitem, key, ff.cleaned_data[key])
                                print('{}: {}'.format(key, ff.cleaned_data[key]))
                                print(type(ff.cleaned_data[key]))
                        else:
                            print(ff.errors)
                        vitem.save()
                    elif 'btn_to_fix' in request.POST:
                        vitem.to_fix = True
                        vitem.fixed = False
                        vitem.dias_status = 'На доработке'
                        vitem.save()
                        newChatMessage(vitem, '{}: {}'.format('На доработку', request.POST['fix_comment']), request.user.extendeduser)
                    elif 'btn_fixed' in request.POST:
                        vitem.to_fix = False
                        vitem.fixed = True
                        vitem.dias_status = 'Доработано'
                        vitem.save()
                        newChatMessage(vitem, '{}: {}'.format('Доработано', request.POST['fix_comment']), request.user.extendeduser)
                    elif 'btn_take_to' in request.POST:
                        vitem.case_officer = request.user.extendeduser
                        vitem.save()
                    elif 'btn_add_comment' in request.POST and len(request.POST['chat_message']) > 0:                    
                        newChatMessage(vitem, request.POST['chat_message'], request.user.extendeduser)

                    return redirect(reverse('vitem', args=[vitem_id]))
            else:
                context['err_txt'] = 'У вас недостаточно прав на просмотр данной страницы'
    
    return render(request, 'verification/404.html', context)

def newChatMessage(vitem, message, author):
    new_msg = models.VitemChat()
    new_msg.vitem = vitem
    new_msg.msg = message
    new_msg.author = author
    new_msg.save()

@login_required
def agent_form(request, agent_id=None):
    if request.user.extendeduser.user_role.role_name == 'FinAgent':
        agent_organization = models.OrganizationWithRole.objects.filter(organization_role = 'ФинАгент')
    elif request.user.extendeduser.user_role.role_name == 'FinBroker':
        agent_organization = models.OrganizationWithRole.objects.filter(organization_role = 'ФинБрокер')
    elif request.user.extendeduser.user_role.role_lvl < 3: # уровень роли сотрудников АиС и Админа - 2 и 1 соответственно
        agent_organization = models.OrganizationWithRole.objects.all()
    
    if request.method == 'POST':
        form = forms.PersonForm(data=request.POST)
        if form.is_valid():
            created_person = form.save()
            agent_role = models.PersonWithRole()
            agent_role.person = created_person
            agent_role.person_role = 'Агент'
            agent_role.author = request.user.extendeduser
            if 'related_organization' in request.POST:
                agent_role.related_organization = models.OrganizationWithRole.objects.get(id = request.POST['related_organization'])
            agent_role.save()
            vi = models.VerificationItem()
            vi.person = agent_role
            vi.dias_status = 'Новая'
            vi.author = request.user.extendeduser
            vi.save()
            return redirect(reverse('scan_upload', args=[vi.id]))
    else:
        if agent_id:
            person = models.Person.objects.filter(id = agent_id)
            if len(person) > 0:
                print(person)
                form = forms.PersonForm(instance=person[0])
            else:
                return render(request, 'verification/404.html')
        else:
            form = forms.PersonForm()
    return render(request, 'verification/forms/objects/agent_form.html', {'page_title': 'Создание агента', 'form': form, 'org_list': agent_organization})

@login_required
def staff_form(request, staff_id=None):
    if request.user.extendeduser.user_role == 'HR' or request.user.extendeduser.user_role.role_lvl < 3:
        staff_organization = models.OrganizationWithRole.objects.filter(organization_role = 'Штатные сотрудники')
    else:
        return render(request, 'verification/404.html', {'err_txt': 'У вас недостаточно прав на создание заявки'})
    if request.method == 'POST':
        form = forms.PersonForm(data=request.POST)
        if form.is_valid():
            created_person = form.save()
            staff_role = models.PersonWithRole()
            staff_role.person = created_person
            staff_role.person_role = 'Штатный сотрудник'
            staff_role.author = request.user.extendeduser
            if 'related_organization' in request.POST:
                staff_role.related_organization = models.OrganizationWithRole.objects.get(id = request.POST['related_organization'])
            staff_role.save()
            vi = models.VerificationItem()
            vi.person = staff_role
            vi.dias_status = 'Новая'
            vi.author = request.user.extendeduser
            vi.save()
            return redirect(reverse('scan_upload', args=[vi.id]))
    else:
        if staff_id:
            person = models.Person.objects.filter(id = agent_id)
            if len(person) > 0:
                print(person)
                form = forms.PersonForm(instance=person[0])
            else:
                return render(request, 'verification/404.html')
        else:
            form = forms.PersonForm()
    return render(request, 'verification/forms/objects/staff_form.html', {'page_title': 'Создание штатного сотрудника', 'form': form, 'org_list': staff_organization})



@login_required
def scan_upload(request, vitem_id=None):
    if request.method == 'GET':
        vitem = models.VerificationItem.objects.filter(id = vitem_id)
        if len(vitem) > 0:
            if vitem[0].person:
                model_name = 'PersonWithRole'
                model_id = vitem[0].person.id
                obj_name = vitem[0].person.person.fio
                doc_types = ['Паспорт 1 страница', 'Паспорт 2 страница', 'Анкета', 'Иной документ']
            else:
                model_name = 'OrganizationWithRole'
                model_id = vitem[0].organization.id
                obj_name = vitem[0].organization.organization.full_name
                doc_types = ['Устав', 'Свидетельство о гос.рег', 'Постановка на налоговый учет', 'Анкета', 'Иной документ']
            scan_q = models.DocStorage.objects.filter(model_id = int(model_id), model_name = model_name)
        else:
            return render(request, 'verification/404.html')
        form = forms.DocStorageForm()
        return render(request, 'verification/forms/scan_upload_form.html', {'page_title': 'Загрузка документов', 'model_name': model_name, 'model_id': model_id, 'obj_name': obj_name, 'vitem_id': vitem_id, 'scan_q': scan_q, 'doc_types': doc_types})
    else:
        if 'btn_upload' in request.POST:
            if request.FILES:
                form = forms.DocStorageForm(request.POST, request.FILES)
                if form.is_valid():
                    form.save()
            return redirect(reverse('scan_upload', args=[vitem_id]))

        elif 'btn_save' in request.POST:
            vi = models.VerificationItem.objects.get(id = vitem_id)
            vi.is_filled = True
            vi.save()
            return redirect('index')
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
    if vitem_id:
        vitem = models.VerificationItem.objects.get(id=vitem_id)
        if request.method == 'GET':
            context = {}
            context['vitem'] = vitem
            if vitem.person:
                context['person'] = vitem.person
            else:
                context['organization'] = vitem.organization
            if request.method == 'POST':
                pass
            else:
                context['form'] = forms.VerificationItemForm(instance=vitem)
            return render(request, 'verification/forms/vitem_form.html', context)
        else:
            if 'btn_save' in request.POST:
                pass
            elif 'btn_to_fix' in request.POST:
                vitem.to_fix = True
                vitem.fixed = False
                vitem.dias_status = 'На доработке'
                vitem.save()
            elif 'btn_fixed' in request.POST:
                vitem.to_fix = False
                vitem.fixed = True
                vitem.dias_status = 'Доработано'
                vitem.save()
            elif 'btn_take_to' in request.POST:
                vitem.case_officer = request.user.extendeduser
                vitem.save()
            return redirect(reverse('vitem', args=[vitem_id]))
    else:
        return render(request, 'verification/404.html')


@login_required
def agent_form(request):
    if request.user.extendeduser.user_role.role_name == 'FinAgent':
        agent_organization = models.OrganizationWithRole.objects.filter(organization_role == 'ФинАгент')
    elif request.user.extendeduser.user_role.role_name == 'FinBroker':
        agent_organization = models.OrganizationWithRole.objects.filter(organization_role == 'ФинБрокер')
    elif request.user.extendeduser.user_role.role_lvl < 3: # уровень роли сотрудников АиС и Админа - 2 и 1 соответственно
        agent_organization = models.OrganizationWithRole.objects.all()
    if request.method == 'POST':
        form = forms.PersonForm(data=request.POST)
        if form.is_valid():
            created_person = form.save()
            agent_role = models.PersonWithRole()
            agent_role.person = created_person
            agent_role.person_role = 'Агент'
            agent_role.author = models.ExtendedUser.objects.get(id = request.user.id)
            if 'related_organization' in request.POST:
                agent_role.related_organization = models.OrganizationWithRole.objects.get(id = request.POST['related_organization'])
            agent_role.save()
            vi = models.VerificationItem()
            vi.person = agent_role
            vi.dias_status = 'Новая'
            vi.author = models.ExtendedUser.objects.get(id = request.user.id)
            vi.save()
            return redirect(reverse('scan_upload', args=[vi.id]))
    else:
        form = forms.PersonForm()
    print(form.errors)
    return render(request, 'verification/forms/agent_form.html', {'page_title': 'Создание агента', 'form': form, 'org_list': agent_organization})

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
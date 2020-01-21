from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.urls import reverse

from . import models
from . import forms
from . import views_utils

def owr_call(request, owr_id, create_title, update_title):
    if views_utils.accessing(owr_id, 'PersonWithRole', request.user):
        context = get_owr_context(request, owr_id, create_title, update_title)
        if request.method == 'POST':
            pass

        return render(request, 'verification/forms/common/organization_form_common.html', context)
    else:
        context = views_utils.get_base_context(request.user)
        context['err_txt'] = 'Запрашиваемая страница не существует или у Вас недостаточно прав на ее просмотр'
        return render(request, 'verification/404.html', context)


def get_owr_context(request, owr_id, create_title, update_title):
    context = views_utils.get_base_context(request.user)
    vitem = models.VerificationItem.objects.filter(organization__id = owr_id)
    if len(vitem) > 0:
        context['vitem_id'] = vitem[0].id

    context['doc_types'] = ['Скан анкеты', 'Скан устава', 'Скан свидетельства о гос.рег.', 'Скан свидетельства о постановке на налоговый учет', 'Иной документ']
    if owr_id:
        owr = models.OrganizationWithRole.objects.filter(id = owr_id)
        if len(owr) > 0 :
            if views_utils.accessing(owr[0], vitem[0], request.user):
                organization = owr[0].organization
                form = forms.OrganizationForm(instance=organization)
                context['page_title'] = update_title
                context['owr'] = owr[0]
                context['object_title'] = f"{context['owr'].organization.full_name} ({context['page_title']})"
                context['ceo'] = models.PersonWithRole.objects.filter(related_organization__id = owr[0].id, person_role = 'Ген. директор')
                context['bens'] = models.PersonWithRole.objects.filter(related_organization__id = owr[0].id, person_role = 'Бенефициар')
                context['scan_list'] = models.DocStorage.objects.filter(model_id = owr[0].organization.id, model_name = 'Organization', to_del = False)
                if request.user.extendeduser.user_role.role_lvl <= 3:
                    context['deleted_scan_list'] = models.DocStorage.objects.filter(model_id = owr[0].organization.id, model_name = 'Organization', to_del = True)
    else:
        form = forms.OrganizationForm()
        context['page_title'] = create_title
    context['form'] = form
    return context


def pwr_call(request, pwr_id, owr_id, pwr_role, rel_pwr_type):
    if views_utils.accessing(pwr_id, 'PersonWithRole', request.user):
        context = get_pwr_context(request, pwr_id, owr_id, pwr_role, rel_pwr_type)
        if request.method == 'POST':
            if pwr_id:
                context['form'] = forms.PersonForm(data=request.POST, instance=context['pwr'].person)
            else:
                context['form'] = forms.PersonForm(data=request.POST)

            if context['form'].is_valid():
                if pwr_id:
                    if context['pwr'].related_organization.id != request.POST['related_organization']:
                        context['pwr'].related_organization = models.OrganizationWithRole.objects.get(id = request.POST['related_organization'])
                        context['pwr'].save()
                    updated_person = context['form'].save(commit=False)
                    views_utils.update_logger('Person', updated_person.id, 'Обновление записи', request.user.extendeduser, updated_person)
                    updated_person = context['form'].save()
                else:
                    new_person = context['form'].save()
                    views_utils.update_logger('Person', new_person.id, '', request.user.extendeduser)
                    pwr = models.PersonWithRole()
                    pwr.person = new_person
                    pwr.person_role = pwr_role
                    pwr.author = request.user.extendeduser
                    if 'related_organization' in request.POST:
                        pwr.related_organization = models.OrganizationWithRole.objects.get(id = request.POST['related_organization'])
                    pwr.save()
                    context['pwr'] = pwr
                    views_utils.update_logger('PersonWithRole', context['pwr'].id, '', request.user.extendeduser)
                if pwr_role == 'Агент':
                    view_name = 'detailing-agent'
                elif pwr_role == 'Штатный сотрудник':
                    view_name = 'detailing-staff'
                elif pwr_role == 'Ген. директор':
                    view_name = 'detailing-ceo'
                else:
                    view_name = 'detailing-ben'
                
                target_id = [context['pwr'].id]
                if owr_id:
                    target_id.insert(0, owr_id)
                return redirect(reverse(view_name, args=[x for x in target_id]))
        
        if pwr_role in ['Ген. директор', 'Бенефициар'] and pwr_id:
            pwr_is_filled = True
            scan_list = models.DocStorage.objects.filter(model_name = 'Person', model_id = context['pwr'].person.id).exclude(to_del = True)
            for doc_type in context['doc_types'][:-1]:
                if scan_list.filter(doc_type = doc_type).count() == 0:
                    pwr_is_filled = False
            if pwr_is_filled:
                if context['owr'].organization_type == 'Партнер':
                    context['owr_href'] = {'view':'detailing-partner', 'view_id': owr_id}
                elif context['owr'].organization_type == 'Контрагент':
                    context['owr_href'] = {'view':'detailing-counterparty', 'view_id': owr_id}
        return render(request, 'verification/forms/common/person_form_common.html', context)
    else:
        context = views_utils.get_base_context(request.user)
        context['err_txt'] = 'Запрашиваемая страница не существует или у Вас недостаточно прав на ее просмотр'
        return render(request, 'verification/404.html', context)

def get_pwr_context(request, pwr_id, owr_id, pwr_role, rel_pwr_type):
    context = views_utils.get_base_context(request.user)
    context['doc_types'] = ['Паспорт 1 страница', 'Паспорт 2 страница', 'Анкета', 'Иной документ']
    if owr_id:
        context['owr'] = models.OrganizationWithRole.objects.get(id=owr_id)
    if pwr_id:
        context['pwr'] = models.PersonWithRole.objects.filter(id = pwr_id)[0]

    context['pwr_role'] = pwr_role
    person_organizations = models.OrganizationWithRole.objects.all()
    if pwr_id:
        person_organizations = person_organizations.filter(id = context['pwr'].related_organization.id)
    elif request.user.extendeduser.user_role == 'HR':
        person_organizations = person_organizations.filter(organization_role = 'Штатные сотрудники')
    elif request.user.extendeduser.user_role.role_lvl > 3:
        person_organizations = person_organizations.filter(organization_role = rel_pwr_type)
    context['org_list'] = person_organizations
    if pwr_id:
        context['form'] = forms.PersonForm(instance=context['pwr'].person)
        context['scan_list'] = models.DocStorage.objects.filter(model_id = context['pwr'].person.id, model_name = 'Person', to_del = False)
        if request.user.extendeduser.user_role.role_lvl <= 3:
            context['deleted_scan_list'] = models.DocStorage.objects.filter(model_id = context['pwr'].person.id, model_name = 'Person', to_del = True)
        if pwr_role in ['Агент', 'Штатный сотрудник']:
            vitem = models.VerificationItem.objects.filter(person__id = pwr_id)[0]
        else:
            vitem = models.VerificationItem.objects.filter(organization__id = owr_id)[0]
        context['vitem_id'] = vitem.id
        context['vitem_is_filled'] = vitem.is_filled
        context['page_title'] = pwr_role
        context['object_title'] = context['pwr'].person.fio
    else:
        context['form'] = forms.PersonForm()
        context['page_title'] = f'Новый {pwr_role}'
    return context
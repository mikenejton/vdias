
from django.shortcuts import render, redirect
from django.urls import reverse
from django.db.models import Q

from . import models
from . import forms
from . import views_utils

def owr_call(request, owr_id, create_title, update_title):
    context = views_utils.get_base_context(request.user)
    if views_utils.accessing(owr_id, 'OrganizationWithRole', request.user):
        context['template'] = 'verification/forms/common/organization_form_common.html'
        context = {**context, **get_owr_context(request, owr_id, create_title, update_title)}
        if 'err_txt' not in context:
            if request.method == 'POST':
                if owr_id:
                    context['form'] = forms.OrganizationForm(data=request.POST, instance=context['owr'].organization)
                else:
                    context['form'] = forms.OrganizationForm(data=request.POST)
                
                if context['form'].is_valid():
                    if owr_id:
                        updated_organization = context['form'].save(commit=False)
                        if 'division' in request.POST:
                            context['owr'].division = models.Division.objects.get(id = request.POST['division'])
                            context['owr'].save()
                        views_utils.update_logger('Organization', updated_organization.id, 'Обновление записи', request.user.extendeduser, updated_organization)
                        updated_organization = context['form'].save()

                    else:
                        new_org = context['form'].save()
                        views_utils.update_logger('Organization', new_org.id, '', request.user.extendeduser)
                        owr = models.OrganizationWithRole()
                        owr.organization = new_org
                        owr.role = models.ObjectRole.objects.get(role_name = update_title)
                        if update_title == 'Партнер':
                            owr.organization_type = request.user.extendeduser.user_role.role_name
                        else:
                            owr.organization_type = update_title
                        owr.author = request.user.extendeduser
                        owr.division = models.Division.objects.get(id = request.POST['division'])
                        owr.save()
                        views_utils.update_logger('Organization', new_org.id, '', request.user.extendeduser)
                        context['owr'] = owr

                        views_utils.vitem_creator(request, owr, 'organization')

                    view_name = 'detailing-partner' if context['owr'].role.role_name == 'Партнер' else 'detailing-counterparty'
                    context['redirect'] = redirect(reverse(view_name, args=[context['owr'].id]))
                else:
                    context['twins'] = models.OrganizationWithRole.objects.filter(Q(organization__inn = context['form'].data['inn']) | Q(organization__ogrn = context['form'].data['ogrn']))

    else:
        context['err_txt'] = 'Запрашиваемая страница не существует или у Вас недостаточно прав на ее просмотр'
    
    if 'err_txt' in context:
        context['template'] = 'verification/404.html'

    if 'redirect' in context:
        return context['redirect']
    else:
        return render(request, context['template'], context)

def get_owr_context(request, owr_id, create_title, update_title):
    context = {'doc_types': ['Скан анкеты', 'Скан устава', 'Скан свидетельства о гос.рег.', 'Скан свидетельства о постановке на налоговый учет', 'Кронос', 'КонтурФокус', 'ФССП', 'Иной документ']}
    context['req_doc_types']=['Скан анкеты', 'Скан устава', 'Скан свидетельства о гос.рег.', 'Скан свидетельства о постановке на налоговый учет']
    context['unfilled'] = []
    context['divisions'] = models.Division.objects.all()[:2]
    if owr_id:
        vitem = models.VerificationItem.objects.filter(organization__id = owr_id)
        if len(vitem) > 0 and owr_id is not None:
            context['vitem_id'] = vitem[0].id
            context['vitem_is_filled'] = vitem[0].is_filled
            context['dias_status'] = vitem[0].dias_status

        owr = models.OrganizationWithRole.objects.filter(id = owr_id)
        if len(owr) > 0 :
            if owr[0].role.role_name == update_title:
                organization = owr[0].organization
                form = forms.OrganizationForm(instance=organization)
                context['page_title'] = update_title
                context['owr'] = owr[0]
                context['roles'] = models.OrganizationWithRole.objects.filter(organization__id = owr[0].organization.id)
                context['vitem_ready'] = views_utils.is_vitem_ready('organization', context['owr'])
                context['object_title'] = context['owr'].organization.full_name
                context['ceo'] = models.PersonWithRole.objects.filter(related_organization__id = owr[0].id, role__role_name = 'Ген. директор')
                context['bens'] = models.PersonWithRole.objects.filter(related_organization__id = owr[0].id, role__role_name = 'Бенефициар')
                context['scan_list'] = models.DocStorage.objects.filter(model_id = owr[0].organization.id, model_name = 'Organization', to_del = False)
                if request.user.extendeduser.user_role.role_lvl <= 3:
                    context['deleted_scan_list'] = models.DocStorage.objects.filter(model_id = owr[0].organization.id, model_name = 'Organization', to_del = True)
                context['form'] = form
                if not context['vitem_ready']:
                    if len(context['ceo']) == 0:
                        context['unfilled'].append('Укажите Ген.директора')
                    else:
                        context['unfilled'].append('Загрузите все необходимые сканы')
            else:
                context['err_txt'] = 'Запрашиваемый объект не существует'
    else:
        context['page_title'] = create_title
        context['unfilled'].append('Заполните данные организации')
        context['form'] = forms.OrganizationForm()
    return context

def pwr_call(request, pwr_id, owr_id, pwr_role, rel_pwr_type):
    context = views_utils.get_base_context(request.user)
    if views_utils.accessing(pwr_id, 'PersonWithRole', request.user):
        context = {**context, **get_pwr_context(request, pwr_id, owr_id, pwr_role, rel_pwr_type)}
        if request.method == 'POST':
            if pwr_id:
                context['form'] = forms.PersonForm(data=request.POST, instance=context['pwr'].person)
            else:
                context['form'] = forms.PersonForm(data=request.POST)

            if context['form'].is_valid():
                if pwr_id:
                    if context['pwr'].related_organization:
                        if context['pwr'].related_organization.id != request.POST['related_organization']:
                            context['pwr'].related_organization = models.OrganizationWithRole.objects.get(id = request.POST['related_organization'])
                            context['pwr'].save()
                    if 'related_organization' in request.POST:
                        context['pwr'].related_organization = models.Organization.objects.get(id = request.POST['related_organization'])
                        context['pwr'].save()
                    if 'related_manager' in request.POST:
                        context['pwr'].related_manager = models.Manager.objects.get(id = request.POST['related_manager'])
                        context['pwr'].save()

                    updated_person = context['form'].save(commit=False)
                    views_utils.update_logger('Person', updated_person.id, 'Обновление записи', request.user.extendeduser, updated_person)
                    updated_person = context['form'].save()
                else:
                    new_person = context['form'].save()
                    views_utils.update_logger('Person', new_person.id, '', request.user.extendeduser)
                    pwr = models.PersonWithRole()
                    pwr.person = new_person
                    pwr.role = models.ObjectRole.objects.get(role_name=pwr_role)
                    pwr.author = request.user.extendeduser
                    if 'related_organization' in request.POST:
                        pwr.related_organization = models.Organization.objects.get(id = request.POST['related_organization'])
                    pwr.save()
                    views_utils.update_logger('PersonWithRole', pwr.id, '', request.user.extendeduser)
                    context['pwr'] = pwr
                    if pwr_role not in ['Ген. директор', 'Бенефициар']:
                        views_utils.vitem_creator(request, pwr, 'person')
                    elif pwr_role == 'Ген. директор':
                        vitem = models.VerificationItem.objects.filter(person__person = pwr.person)
                        if not len(vitem):
                            vitem = models.VerificationItem.objects.filter(organization__organization = pwr.related_organization)
                        views_utils.vitem_creator(request, pwr, 'person', True, vitem)

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
                context['redirect'] = redirect(reverse(view_name, args=[x for x in target_id]))
            elif not pwr_id:
                person_fio = ' '.join([context['form'].data['last_name'], context['form'].data['first_name'], context['form'].data['patronymic']])
                context['twins'] = models.PersonWithRole.objects.filter(Q(person__pass_sn = context['form'].data['pass_sn']) | Q(person__sneals = context['form'].data['sneals']) | Q(person__phone_number = context['form'].data['phone_number']) | Q(person__fio = person_fio, person__dob = context['form'].data['dob'] ))
                if len(context['twins']):
                    is_new_twin = True
                    for twin in context['twins']:
                        if twin.role == pwr_role:
                            is_new_twin = False
                    if is_new_twin:
                        pwr = models.PersonWithRole()
                        pwr.person = context['twins'][0].person
                        pwr.role = pwr_role
                        pwr.author = request.user.extendeduser
                        if 'related_organization' in request.POST:
                            pwr.related_organization = models.Organization.objects.get(id = request.POST['related_organization'])
                        pwr.save()
                        context['pwr'] = pwr
                        vitem = models.VerificationItem.objects.filter(person__person = pwr.person, is_shadow = False)
                        if pwr_role != 'Бенефициар':
                            views_utils.vitem_creator(request, pwr, 'person', len(vitem), vitem)
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
                        context['redirect'] = redirect(reverse(view_name, args=[x for x in target_id]))

        if pwr_role in ['Ген. директор', 'Бенефициар'] and pwr_id:
            pwr_is_filled = views_utils.required_scan_checking(context['pwr'].person.id, 'person', models.ObjectRole.objects.get(role_name = pwr_role))
            if pwr_is_filled:
                context['owr_href'] = {'view':'detailing-partner' if context['owr'].role.role_name == 'Партнер' else 'detailing-counterparty', 'view_id': owr_id}
            else:
                context['unfilled'].append('Загрузите все необходимые сканы')
        context['template'] = 'verification/forms/common/person_form_common.html'
    else:
        context['err_txt'] = 'Запрашиваемая страница не существует или у Вас недостаточно прав на ее просмотр'

    if 'err_txt' in context:
        context['template'] = 'verification/404.html'
    if 'redirect' in context:
        return context['redirect']
    else:
        return render(request, context['template'], context)

def get_pwr_context(request, pwr_id, owr_id, pwr_role, rel_pwr_type):
    context = {'doc_types': ['Паспорт 1 страница', 'Паспорт 2 страница', 'СНИЛС', 'Видеоприветствие', 'Кронос', 'КонтурФокус', 'ФССП', 'Иной документ']}
    context['req_doc_types']=['Паспорт 1 страница', 'Паспорт 2 страница']
    if pwr_role == 'Агент':
        context['req_doc_types'].append('Видеоприветствие')
    context['unfilled'] = []
    person_organizations = models.OrganizationWithRole.objects.all()
    if request.user.extendeduser.user_role == 'HR' or pwr_role == 'Штатные сотрудники':
        person_organizations = person_organizations.filter(organization_type = 'Штатные сотрудники')
    elif request.user.extendeduser.user_role.role_lvl > 3:
        person_organizations = person_organizations.filter(organization_type = rel_pwr_type)
    context['org_list'] = person_organizations
    if request.user.extendeduser.user_role.role_lvl <= 2:
        context['mngr_list'] = models.Manager.objects.all()
    else:
        context['mngr_list'] = models.Manager.objects.filter(id = 0)
    
    if owr_id:
        context['owr'] = models.OrganizationWithRole.objects.get(id=owr_id)
    if pwr_id:
        pwr = models.PersonWithRole.objects.filter(id = pwr_id)
        if len(pwr):
            context['pwr'] = pwr[0]
            context['roles'] = models.PersonWithRole.objects.filter(person__id = pwr[0].person.id)
            context['vitem_ready'] = views_utils.is_vitem_ready('person', context['pwr'])
            context['pwr_role'] = pwr_role
            if request.user.extendeduser.user_role.role_lvl > 2:
                if context['pwr'].related_organization:
                    context['org_list'] = person_organizations.filter(id = context['pwr'].related_organization.id)
                if context['pwr'].related_manager:
                    context['mngr_list'] = context['mngr_list'].filter(id = context['pwr'].related_manager.id)

            context['form'] = forms.PersonForm(instance=context['pwr'].person)
            context['scan_list'] = models.DocStorage.objects.filter(model_id = context['pwr'].person.id, model_name = 'Person', to_del = False)
            if request.user.extendeduser.user_role.role_lvl <= 3:
                context['deleted_scan_list'] = models.DocStorage.objects.filter(model_id = context['pwr'].person.id, model_name = 'Person', to_del = True)
            if owr_id:
                vitem = models.VerificationItem.objects.filter(organization__id = owr_id)[0]
            if pwr_role in ['Агент', 'Штатный сотрудник', 'Ген. директор', 'Бенефициар']:
                
                person_vitem = models.VerificationItem.objects.filter(person__id = pwr_id)
                if len(person_vitem):
                    vitem = person_vitem[0]
                if not context['vitem_ready']:
                    context['unfilled'].append('Загрузите все необходимые сканы')
            if vitem:
                context['vitem_id'] = vitem.id
                context['vitem_is_filled'] = vitem.is_filled
                context['dias_status'] = vitem.dias_status
            context['page_title'] = pwr_role
            context['object_title'] = context['pwr'].person.fio
            
        else:
            context['err_txt'] = 'Запрашиваемый объект не существует'
    else:
        context['form'] = forms.PersonForm()
        context['page_title'] = f'Новый {pwr_role}'
        context['unfilled'].append('Заполните данные физ.лица')
        
    
    return context

def short_item_call(request, si_id):
    context = views_utils.get_base_context(request.user)
    if views_utils.accessing(si_id, 'ShortItem', request.user):
        context['template'] = 'verification/forms/common/short_item_form_common.html'
        context = {**context, **get_short_item_context(request, si_id)}
        if request.method == 'POST':            
            if si_id:
                context['form'] = forms.ShortItemForm(data=request.POST, instance=context['short_item'])
            else:
                context['form'] = forms.ShortItemForm(data=request.POST)
            
            if context['form'].is_valid():
                if si_id:
                    updated_short_item = context['form'].save(commit=False)
                    views_utils.update_logger('ShortItem', updated_short_item.id, 'Обновление записи', request.user.extendeduser, updated_short_item)
                    updated_short_item = context['form'].save()
                else:
                    
                    new_short_item = context['form'].save()
                    views_utils.update_logger('ShortItem', new_short_item.id, '', request.user.extendeduser)
                    context['short_item'] = new_short_item
                    views_utils.vitem_creator(request, new_short_item, 'short_item')
                
                view_name = 'detailing-short-item'
                context['redirect'] = redirect(reverse(view_name, args=[context['short_item'].id]))
    else:
        context['err_txt'] = 'Запрашиваемая страница не существует или у Вас недостаточно прав на ее просмотр'

    if 'err_txt' in context:
        context['template'] = 'verification/404.html'

    if 'redirect' in context:
        return context['redirect']
    else:
        return render(request, context['template'], context)

def get_short_item_context(request, si_id):
    context = {'unfilled': []}
    if si_id:
        short_items = models.ShortItem.objects.filter(id = si_id)
        if len(short_items):
            context['short_item'] = short_items[0]
            context['vitem_ready'] = views_utils.is_vitem_ready('short_item', context['short_item'])
            context['form'] = forms.ShortItemForm(instance=context['short_item'])
            context['vitem_is_filled'] = True
            context['page_title'] = f"{context['short_item'].role} (short)"
            vitem = models.VerificationItem.objects.filter(short_item__id = si_id)
            if len(vitem):
                context['vitem_id'] = vitem[0].id
        else:
            context['err_txt'] = 'Запрашиваемый объект не существует'

    else:
        context['form'] = forms.ShortItemForm()
        context['page_title'] = f'Новая'
        context['unfilled'].append('Заполните данные короткой заявки')

    return context

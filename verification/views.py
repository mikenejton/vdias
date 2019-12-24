from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required

from . import models
from . import forms


# Логирование действий пользователя
def update_logger(model_name, pk, action, username, new_set=False, old_set=''):
    if not new_set:
        new_dl = models.DataLogger()
        new_dl(model_name=model_name, model_id=pk, action='Создание записи', author=username)
    else:
        changes = []
        for i in new_set._meta.get_fields():
            print('OLD {} - NEW {}'.format(getattr(old_set, i.name), getattr(new_set, i.name)))
            if getattr(old_set, i.name) != getattr(new_set, i.name):
                changes.append([i.name, getattr(new_set, i.name), getattr(old_set, i.name)])
        print(changes)
        if len(changes) > 0:
            for i in changes:
                new_dl = models.DataLogger()
                new_dl(model_name=model_name, model_id=pk, action='Обновление записи', field_name=i[0], new_value=i[1], old_value=i[2], author=username)
                
@login_required
def index(request):
    user_access = [models.ExtendedUser.objects.get(id=request.user.id).user_role.role_name, models.ExtendedUser.objects.get(id=request.user.id).access_lvl]
    ex_user = models.ExtendedUser.objects.get(user=request.user)
    return render(request, 'verification/index.html', {'page_title': 'Home', 'u_data': user_access, 'ex_user': ex_user})

@login_required
def find_vitem(request):
    user_access = [models.ExtendedUser.objects.get(id=request.user.id).user_role.role_name, models.ExtendedUser.objects.get(id=request.user.id).access_lvl]
    ex_user = models.ExtendedUser.objects.get(user=request.user)
    if request.POST:
        if request.POST['person']:
            result = models.VerificationItem.objects.filter(person__person__fio__icontains = request.POST['person'].upper())
        else:
            result = models.VerificationItem.objects.filter(organization__organization__full_name__icontains = request.POST['person'].upper())
    return render(request, 'verification/find_item_result.html', {'page_title': 'Поиск заявок', 'u_data': user_access, 'ex_user': ex_user, 'result': result})

@login_required
def create_item(request):
    user_access = [models.ExtendedUser.objects.get(id=request.user.id).user_role.role_name, models.ExtendedUser.objects.get(id=request.user.id).access_lvl]
    ex_user = models.ExtendedUser.objects.get(user=request.user)
    if request.method == 'GET':
        
        return render(request, 'verification/create_item.html', {'page_title': 'Создание заявки', 'ex_user': ex_user})

    elif request.POST['item_type'] == 'Агент':        
        
        return redirect('create-agent')

    elif request.POST['item_type'] == 'Партнер':

        return redirect('index')

    elif request.POST['item_type'] == 'Штатный сотрудник':
        
        return redirect('index')

    elif request.POST['item_type'] == 'Контрагент':
        
        return redirect('index')

@login_required
def agent_form(request):
    if request.method == 'POST':
        form = forms.PersonForm(data=request.POST)
        print(request.POST)
        if form.is_valid():
            created_person = form.save()
            agent_role = models.PersonWithRole()
            agent_role.person = created_person
            agent_role.person_role = 'Агент'
            agent_role.author = models.ExtendedUser.objects.get(id = request.user.id)
            if 'related_organization' in request.POST != None:
                agent_role.related_organization = models.OrganizationWithRole.objects.get(id = request.POST['related_organization'])
            agent_role.save()
            vi = models.VerificationItem()
            vi.person = agent_role
            vi.dias_status = 'Новая'
            vi.author = models.ExtendedUser.objects.get(id = request.user.id)
            vi.save()
            return redirect('index')
            # редирект на заполнение сканов к агенту
        else:
            print(form.errors)
            return redirect('index')
    else:
        form = forms.PersonForm
        if request.user.extendeduser.user_role.role_name == 'FinAgent':
            agent_organization = models.OrganizationWithRole.objects.filter(organization_role == 'ФинАгент')
        elif request.user.extendeduser.user_role.role_name == 'FinBroker':
            agent_organization = models.OrganizationWithRole.objects.filter(organization_role == 'ФинБрокер')
        elif request.user.extendeduser.user_role.role_lvl < 3: # уровень роли сотрудников АиС и Админа - 2 и 1 соответственно
            agent_organization = models.OrganizationWithRole.objects.all()
        return render(request, 'verification/agent_form.html', {'page_title': 'Создание агента', 'form': form, 'org_list': agent_organization})

@login_required
def scan_upload(request, vitem_id):
    if request.method == 'GET':
        vitem = models.VerificationItem.objects.get(id = vitem_id)
        if vitem.person:
            model_name = 'PersonWithRole'
            model_id = vitem.person.id
        else:
            model_name = 'OrganizationWithRole'
            model_id = vitem.organization.id
        pass
        # return render('verification/scan_upload_form.html', 'page_title': 'Загрузка документов', 'model_name': model_name, 'model_id': model_id, 'vitem_id': vitem_id)
    else:
        pass
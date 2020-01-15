from . import models

class UserStats:
    def __init__(self):
        pass

# Базовый контекст для меню
def get_base_context(user):
    context = {}
    stats = UserStats()
    stats.q_all = models.VerificationItem.objects.all()
    stats.q_new = stats.q_all.filter(dias_status = 'Новая') 
    stats.q_main = stats.q_all.filter(case_officer__user = user)
    stats.q_at_work = stats.q_all.filter(dias_status = 'В работе')
    stats.q_to_fix = stats.q_all.filter(to_fix = True)
    stats.q_fixed = stats.q_all.filter(fixed = True)
    stats.q_finished = stats.q_all.filter(dias_status__in=['Отказ', 'Одобрено', 'Одобрено, особый контроль'])
    if user.extendeduser.user_role.role_lvl == 2:
        stats.q_new = stats.q_all.filter(dias_status = 'Новая') #????????? штатник и контрагент?
    if user.extendeduser.user_role.role_lvl == 3:
        stats.q_all = stats.q_all.filter(case_officer__user_role__role_lvl = 3) #????????? не штатник и не контрагент?
        stats.q_new = stats.q_all.filter(dias_status = 'Новая')
        stats.q_at_work = stats.q_main.filter(dias_status = 'В работе')
        stats.q_to_fix = stats.q_main.filter(to_fix = True)
        stats.q_fixed = stats.q_main.filter(fixed = True)
        stats.q_finished = stats.q_main.filter(dias_status__in=['Отказ', 'Одобрено', 'Одобрено, особый контроль'])
    elif user.extendeduser.user_role.role_lvl >= 4:
        stats.q_all = stats.q_all.filter(author__user_role = user.extendeduser.user_role)
        stats.q_main = stats.q_all.filter(author__user = user)
        stats.q_at_work = stats.q_main.filter(dias_status = 'В работе')
        stats.q_to_fix = stats.q_main.filter(to_fix = True)
        stats.q_fixed = stats.q_main.filter(fixed = True)
        stats.q_finished = stats.q_main.filter(dias_status__in=['Отказ', 'Одобрено', 'Одобрено, особый контроль'])
    context['stats'] = stats
    return context
    
# Логирование действий пользователя
def update_logger(model_name, pk, action, username, new_set=False):
    if not new_set:
        new_dl = models.DataLogger(model_name=model_name, model_id=pk, action='Создание записи', author=username)
        new_dl.save()
    else:
        changes = []
        old_set = getattr(models, model_name).objects.get(id=pk)
        for i in new_set._meta.fields:
            if getattr(old_set, i.name) != getattr(new_set, i.name):
                changes.append([i.name, getattr(new_set, i.name), getattr(old_set, i.name)])
        if len(changes) > 0:
            for i in changes:
                new_dl = models.DataLogger(model_name=model_name, model_id=pk, action='Обновление записи', field_name=i[0], new_value=i[1], old_value=i[2], author=username)
                new_dl.save()

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
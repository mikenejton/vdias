from . import models
from django.db.models import Q
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
        stats.q_new = stats.q_all.filter(dias_status = 'Новая').filter(Q(person__person_role = 'Штатный сотрудник') | Q(organization__organization_role = 'Контрагент')) #????????? штатник и контрагент?
    if user.extendeduser.user_role.role_lvl == 3:
        stats.q_all = stats.q_all.exclude(Q(person__person_role = 'Штатный сотрудник') | Q(organization__organization_role = 'Контрагент')) #????????? не штатник и не контрагент?
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
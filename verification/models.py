from datetime import datetime
from django.db import models
from django.contrib.auth.models import User

# User's extends
class UserRole(models.Model):
    role_lvl = models.IntegerField('Уровень роли ')
    role_name = models.CharField('Роль', max_length = 200)
    role_description = models.CharField('Описание', max_length = 1000)
    def __str__(self):
        return self.role_name

class ExtendedUser(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    user_role = models.ForeignKey(UserRole, on_delete=models.PROTECT)
    access_lvl = models.IntegerField('Уровень доступа')
    def __str__(self):
        return ' '.join(filter(None, [self.user.last_name, self.user.first_name]))
# -----------------------------------------------------------

# Базовые модели
class Person(models.Model):
    fio = models.CharField('ФИО', max_length=500, blank=True)
    last_name = models.CharField('Фамилия', max_length=300)
    first_name = models.CharField('Имя', max_length=300)
    patronymic = models.CharField('Отчетство', max_length=300, blank=True, null=True)
    dob = models.DateField('Дата рождения', blank=True, null=True)
    pob = models.CharField('Место рождения', max_length=300, blank=True, null=True)
    adr_reg = models.CharField('Адрес регистрации', max_length=500, blank=True, null=True)
    adr_fact = models.CharField('Адрес проживания', max_length=500, blank=True, null=True)
    pass_sn = models.CharField('Серия-номер паспорта', max_length=11, blank=True, null=True, unique=True)
    pass_date = models.DateField('Дата выдачи', blank=True, null=True)
    pass_org = models.CharField('Кем выдан', max_length=500, blank=True, null=True)
    pass_code = models.CharField('Код подразделения', max_length=7, blank=True, null=True)
    sneals = models.CharField('СНИЛС', max_length = 14, blank=True, null=True, unique=True)
    phone_number = models.CharField('Телефон', max_length = 11, blank=True, null=True, unique=True)
    email = models.EmailField('Email', blank=True, null=True)
    created = models.DateTimeField('Дата создания', auto_now_add=True)
    author = models.ForeignKey(ExtendedUser, on_delete=models.PROTECT, verbose_name='Автор')
    def save(self, *args, **kwargs):
        self.fio = ' '.join(filter(None, [self.last_name, self.first_name, self.patronymic])).upper()
        super().save(*args, **kwargs)
    
    def __str__(self):
        return self.fio
    
    class Meta:
        unique_together = [['last_name', 'first_name', 'patronymic', 'dob']]
        verbose_name = 'Физ.лицо'

class Organization(models.Model):
    org_form = models.CharField('Орг форма', max_length = 100)
    full_name = models.CharField('Название', max_length = 500)
    ceo = models.ForeignKey(Person, on_delete=models.PROTECT, blank=True, null=True, verbose_name='Ген.директор')
    adr_reg = models.CharField('Юридический адрес', max_length=500, blank=True, null=True)
    adr_fact = models.CharField('Фактический адрес', max_length=500, blank=True, null=True)
    inn = models.CharField('ИНН', max_length = 12, blank=True, null=True)
    ogrn = models.CharField('ОГРН', max_length = 15, blank=True, null=True)
    phone_number = models.CharField('Телефон', max_length = 11, blank=True, null=True)
    email = models.EmailField('Email', blank=True, null=True)
    created = models.DateTimeField('Дата создания', auto_now_add=True)
    author = models.ForeignKey(ExtendedUser, on_delete=models.PROTECT, verbose_name='Автор')
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
    
    def __str__(self):
        return '{}, ИНН {}'.format(self.full_name, self.inn)

# -----------------------------------------------------------

# Модели для верификации
class OrganizationWithRole(models.Model):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)
    organization_role = models.CharField('Роль', max_length=300)
    verificated = models.BooleanField('Верифицировано', default=False)
    created = models.DateTimeField('Дата создания', auto_now_add=True)
    author = models.ForeignKey(ExtendedUser, on_delete=models.PROTECT, verbose_name='Автор')
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
    
    def __str__(self):
        return '{}, {}'.format(self.organization.full_name, self.organization_role)

class PersonWithRole(models.Model):
    person = models.ForeignKey(Person, on_delete=models.CASCADE)
    person_role = models.CharField('Роль', max_length=300)
    verificated = models.BooleanField('Верифицирован', default=False)
    related_organization = models.ForeignKey(OrganizationWithRole, on_delete=models.PROTECT, blank=True, null=True)
    created = models.DateTimeField('Дата создания', auto_now_add=True)
    author = models.ForeignKey(ExtendedUser, on_delete=models.PROTECT, verbose_name='Автор')
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

    def __str__(self):
        return str(self.person)

class VerificationItem(models.Model):
    person = models.ForeignKey(PersonWithRole, on_delete=models.CASCADE, blank = True, null = True)
    organization = models.ForeignKey(OrganizationWithRole, on_delete=models.CASCADE, blank = True, null = True)
    is_filled = models.BooleanField('Заявка заполнена', default=False)
    dias_status = models.CharField('Статус проверки', max_length = 300)
    to_fix = models.BooleanField('На доработке', default=False)
    fixed = models.BooleanField('Доработано', default=False)
    dias_comment = models.TextField('Комментарий ДИАС', blank=True, null=True)
    case_officer = models.ForeignKey(ExtendedUser, on_delete=models.PROTECT, related_name='CaseOfficer', blank=True, null=True, verbose_name='Исполнитель')
    cronos = models.TextField('Кронос', blank=True, null=True, default='')
    fms_not_ok = models.BooleanField('ФМС', blank=True, null=True)
    rosfin = models.BooleanField('Росфинмониторинг', blank=True, null=True)
    fssp = models.TextField('ФССП', blank=True, null=True, default='')
    docs_full = models.BooleanField('Полнота и качество документов', blank=True, null=True)
    bankruptcy = models.TextField('Сайт по банкротству', blank=True, null=True, default='')
    сourt = models.TextField('Суды', blank=True, null=True, default='')
    contur_focus = models.TextField('Контур-Фокус', blank=True, null=True, default='')
    affiliation = models.TextField('Проверка на аффилированность', blank=True, null=True, default='')
    created = models.DateTimeField('Дата создания', auto_now_add=True)
    author = models.ForeignKey(ExtendedUser, on_delete=models.PROTECT, verbose_name='Автор')
    def save(self, *args, **kwargs):
        if self.fixed:
            self.to_fix = False
        if self.to_fix:
            self.fixed = False
        super().save(*args, **kwargs)
        return self.id
    
    def __str__(self):
        caption = ''
        if self.person:
            caption = str(self.person)
        elif self.organization:
            caption = str(self.organization)
        else:
            caption = 'No verification item..'
        return caption

class VitemChat(models.Model):
    vitem = models.ForeignKey(VerificationItem, on_delete=models.CASCADE)
    msg = models.TextField('Сообщение')
    author = models.ForeignKey(ExtendedUser, on_delete=models.PROTECT, related_name='MsgAuthor', verbose_name='Пользователь')
    created = models.DateTimeField('Дата создания', auto_now_add=True)

# -----------------------------------------------------------

# Хранилище документов
def doc_path_maker(instance, filename):
    timestamp = datetime.strftime(datetime.now(), '%d%m%Y_%H%M%S')
    if instance.model_name == 'PersonWithRole':
        obj_name = PersonWithRole.objects.get(id = instance.model_id).person.fio
    else:
        obj_name = OrganizationWithRole.objects.get(id = instance.model_id).full_name
    f_name = ''.join([instance.doc_type.replace(' ', '_'), '_', timestamp, '.', filename.split('.')[-1]])
    return '{}/{}_{}/{}'.format(instance.model_name, obj_name, instance.model_id, f_name)

class DocStorage(models.Model):
    model_id = models.CharField('ID модели', max_length = 50)
    model_name = models.CharField('Модель', max_length = 200)
    doc_type = models.CharField('Тип документа', max_length = 300)
    file_name = models.CharField('Имя файла', max_length = 300, blank=True)
    scan_file = models.FileField(upload_to=doc_path_maker, verbose_name='Путь к файлу')
    scan = models.BooleanField('Скан', default=False)
    original = models.BooleanField('Оригинал', default=False)
    accepted = models.BooleanField('Проверен', default=False)
    to_del = models.BooleanField('На удаление', default=False)
    created = models.DateTimeField('Дата создания', auto_now_add=True)
    author = models.ForeignKey(ExtendedUser, on_delete=models.PROTECT, verbose_name='Автор')
    def save(self, *args, **kwargs):
        timestamp = datetime.strftime(datetime.now(), '%d%m%Y_%H%M%S')
        self.file_name = ''.join([self.doc_type.replace(' ', '_'), '_', timestamp, '.', self.scan_file.name.split('.')[-1]])
        super().save(*args, **kwargs)        
    
    def __str__(self):
        return '{} {} {}'.format(self.model_id, self.model_name, self.doc_type)

# -----------------------------------------------------------

# Уведомления пользователя - непонятно, нужно ли
class UserNotification(models.Model):
    user = models.ForeignKey(ExtendedUser, on_delete=models.PROTECT, verbose_name='Пользователь')
    msg_type = models.CharField('Тип уведомления', max_length=300)
    msg = models.TextField('Уведомление')
    msg_author = models.ForeignKey(ExtendedUser, on_delete=models.PROTECT, related_name='NotifyAuthor', verbose_name='Пользователь')
    created = models.DateTimeField('Дата создания', auto_now_add=True)
# -----------------------------------------------------------

# Логирование действий
class DataLogger(models.Model):
    model_name = models.CharField('Модель', max_length = 300, blank=True, null=True)
    model_id = models.BigIntegerField('ID записи', blank=True, null=True)
    action = models.CharField('Действие', max_length=500, null=True, blank=True)
    field_name = models.CharField('Название поля', max_length=300, null=True, blank=True)
    new_value = models.CharField('Новое значение', max_length=500, null=True, blank=True)
    old_value = models.CharField('Старое значение', max_length=500, null=True, blank=True)
    created = models.DateTimeField('Дата создания', auto_now_add=True)
    author = models.ForeignKey(ExtendedUser, on_delete=models.SET_NULL, null=True, verbose_name='Пользователь')
    def __str__(self):
        return '{} {}'.format(self.model_name, self.created)

# -----------------------------------------------------------
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
        return self.user.username
# -----------------------------------------------------------

# Базовые модели
class Person(models.Model):
    fio = models.CharField('ФИО', max_length=500)
    last_name = models.CharField('Фамилия', max_length=300)
    first_name = models.CharField('Имя', max_length=300)
    patronymic = models.CharField('Отчетство', max_length=300, blank=True, null=True)
    dob = models.DateField('Дата рождения', blank=True, null=True)
    pob = models.CharField('Место рождения', max_length=300, blank=True, null=True)
    adr_reg = models.CharField('Адрес регистрации', max_length=500, blank=True, null=True)
    adr_fact = models.CharField('Адрес проживания', max_length=500, blank=True, null=True)
    pass_sn = models.CharField('Серия-номер паспорта', max_length=11, blank=True, null=True)
    pass_date = models.DateField('Дата выдачи', blank=True, null=True)
    pass_org = models.CharField('Кем выдан', max_length=500, blank=True, null=True)
    pass_code = models.CharField('Код подразделения', max_length=7, blank=True, null=True)
    sneals = models.CharField('СНИЛС', max_length = 14, blank=True, null=True)
    phone_number = models.CharField('Телефон', max_length = 11, blank=True, null=True)
    email = models.EmailField('Email', blank=True, null=True)
    created = models.DateTimeField('Дата создания', auto_now_add=True)
    author = models.ForeignKey(ExtendedUser, on_delete=models.PROTECT, verbose_name='Автор')
    def save(self, *args, **kwargs):
        self.fio = ' '.join(filter(None, [self.last_name, self.first_name, self.patronymic]))
        super().save(*args, **kwargs)
    
    def __str__(self):
        return self.fio

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
class PersonWithRole(models.Model):
    person = models.ForeignKey(Person, on_delete=models.CASCADE)
    person_role = models.CharField('Роль', max_length=300)
    verificated = models.BooleanField('Верифицирован')
    releated_organization = models.ForeignKey(Organization, on_delete=models.PROTECT, blank=True, null=True)
    created = models.DateTimeField('Дата создания', auto_now_add=True)
    author = models.ForeignKey(ExtendedUser, on_delete=models.PROTECT, verbose_name='Автор')
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

    def __str__(self):
        return str(self.person)

class OrganizationWithRole(models.Model):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)
    organization_role = models.CharField('Роль', max_length=300)
    verificated = models.BooleanField('Верифицировано')
    created = models.DateTimeField('Дата создания', auto_now_add=True)
    author = models.ForeignKey(ExtendedUser, on_delete=models.PROTECT, verbose_name='Автор')
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
    
    def __str__(self):
        return str(self.organization)

class VerificationItem(models.Model):
    person = models.ForeignKey(PersonWithRole, on_delete=models.CASCADE, blank = True, null = True)
    organization = models.ForeignKey(OrganizationWithRole, on_delete=models.CASCADE, blank = True, null = True)
    dias_status = models.CharField('Статус проверки', max_length = 300)
    to_fix = models.BooleanField('На доработке')
    fixed = models.BooleanField('Доработано')
    dias_comment = models.TextField('Комментарий ДИАС', blank=True, null=True)
    case_officer = models.ForeignKey(ExtendedUser, on_delete=models.PROTECT, related_name='CaseOfficer', blank=True, null=True, verbose_name='Исполнитель')
    created = models.DateTimeField('Дата создания', auto_now_add=True)
    author = models.ForeignKey(ExtendedUser, on_delete=models.PROTECT, verbose_name='Автор')
    def save(self, *args, **kwargs):
        if self.fixed:
            self.to_fix = False
        if self.to_fix:
            self.fixed = False
        super().save(*args, **kwargs)
    
    def __str__(self):
        caption = ''
        if self.person:
            caption = str(self.person)
        elif self.organization:
            caption = str(self.organization)
        else:
            caption = 'No verification item..'
        return caption

# -----------------------------------------------------------

# Хранилище документов
class DocStorage(models.Model):
    model_id = models.CharField('ID', max_length = 50) #model_id формируется из названия модели и "_" id записи модели, прим.: VerificationItem_31, PersonWithRole_227
    doc_type = models.CharField('Тип документа', max_length = 300)
    doc_name = models.CharField('Имя документа', max_length = 300)
    file_name = models.CharField('FileName', max_length = 700)
    file_path = models.CharField('FilePath', max_length = 700)
    scan = models.BooleanField('Скан')
    original = models.BooleanField('Оригинал')
    accepted = models.BooleanField('Проверен')
    created = models.DateTimeField('Дата создания', auto_now_add=True)
    author = models.ForeignKey(ExtendedUser, on_delete=models.PROTECT, verbose_name='Автор')
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)        
    
    def __str__(self):
        return '{} {} {}'.format(self.model_id, self.doc_type, self.doc_name)

# -----------------------------------------------------------

# Уведомления пользователя
class UserNotification(models.Model):
    user = models.ForeignKey(ExtendedUser, on_delete=models.PROTECT, verbose_name='Пользователь')
    msg_type = models.CharField('Тип уведомления', max_length=300)
    msg = models.TextField('Уведомление')
    msg_author = models.ForeignKey(ExtendedUser, on_delete=models.PROTECT, related_name='MsgAuthor', verbose_name='Пользователь')
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
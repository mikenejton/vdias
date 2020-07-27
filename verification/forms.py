from django.forms import ModelForm
from django.core.exceptions import ValidationError
from datetime import datetime
from . import models

class PersonForm(ModelForm):
    class Meta:
        model = models.Person
        fields = '__all__'
    def clean(self):
        cleaned_data=super(PersonForm, self).clean()
        if cleaned_data.get('dob'):
            date_diff = datetime.now().date() - cleaned_data.get('dob')
            if round(date_diff.days/365.25, 0)  < 18:
                raise ValidationError({'dob': 'Возраст менее 18-ти лет!'})
            elif round(date_diff.days/365.25, 0)  > 99:
                raise ValidationError({'dob': 'Возраст более 99-ти лет!'})
            if cleaned_data.get('pass_date'):
                date_diff = cleaned_data.get('pass_date') - cleaned_data.get('dob')
                if round(date_diff.days/365.25, 0)  < 14:
                    raise ValidationError({'pass_date': 'Ошибка в дате выдачи паспорта (разница с датой рождения менее 14 лет!'})
        
class OrganizationForm(ModelForm):
    class Meta:
        model = models.Organization
        fields = '__all__'

class DocStorageForm(ModelForm):
    class Meta:
        model = models.DocStorage
        fields = ('model_id', 'model_name', 'doc_type', 'scan_file', 'author')

class VerificationItemForm(ModelForm):
    class Meta:
        model = models.VerificationItem
        fields = ('status', 'dias_comment', 'case_officer', 'fms_not_ok', 'docs_full', 'reg_checked', 'rosfin', 'cronos', 'cronos_status', 'fssp', 'fssp_status', 'bankruptcy', 'bankruptcy_status', 'court', 'court_status', 'contur_focus', 'contur_focus_status', 'affiliation', 'affiliation_status', 'soc', 'soc_status')

class PersonWithRoleForm(ModelForm):
    class Meta:
        model = models.PersonWithRole
        fields = '__all__'

class OrganizationWithRoleForm(ModelForm):
    class Meta:
        model = models.OrganizationWithRole
        fields = '__all__'

class ShortItemForm(ModelForm):
    class Meta:
        model = models.ShortItem
        fields = '__all__'
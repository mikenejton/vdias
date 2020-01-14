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
        print(type(cleaned_data.get('dob')))
        date_diff = datetime.now().date() - cleaned_data.get('dob')
        if round(date_diff.days/365.25, 0)  < 18:
            raise ValidationError({'dob': 'Возраст менее 18-ти лет!'})
        elif round(date_diff.days/365.25, 0)  > 99:
            raise ValidationError({'dob': 'Возраст более 99-ти лет!'})
        




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
        fields = ('dias_status', 'to_fix', 'fixed', 'dias_comment', 'case_officer', 'cronos', 'fms_not_ok', 'rosfin', 'fssp', 'docs_full', 'bankruptcy', 'сourt', 'contur_focus', 'affiliation')

class PersonWithRoleForm(ModelForm):
    class Meta:
        model = models.PersonWithRole
        fields = '__all__'

class OrganizationWithRoleForm(ModelForm):
    class Meta:
        model = models.OrganizationWithRole
        fields = '__all__'
from django import forms
from django.contrib import auth
from django.contrib.auth.models import User
from django.forms import ModelForm
from Influencers.models import Lead, B2BLead


class LoginForm(forms.Form):
    user_name=forms.CharField(label='UserName',max_length=100)
    password=forms.CharField(label='Password',widget=forms.PasswordInput)


    def clean_username(self):
        data=self.cleaned_data['user_name']
        if not data:
            raise forms.ValidationError('Please enter username')
        return data
    def clean_password(self):
        data=self.cleaned_data['password']
        if not data:
            raise forms.ValidationError('Please enter your password')
        return data

    def clean(self):
        try:
            username = User.objects.get(username=self.cleaned_data['user_name']).username
        except User.DoesNotExist:
            raise forms.ValidationError(("No such user registered"))
        password = self.cleaned_data['password']

        self.user = auth.authenticate(username=username, password=password)
        if self.user is None or not self.user.is_active:
            raise forms.ValidationError("username or password is incorrect")
        return self.cleaned_data


class LeadForm(ModelForm):
    class Meta:
        model=Lead
        exclude=['created_at','updated_at','created_by','created_on','span']
    def __init__(self, *args, **kwargs):
        super(LeadForm, self).__init__(*args, **kwargs)
        self.fields['response'].required = False


class B2BLeadForm(ModelForm):
    class Meta:
        model = B2BLead
        exclude = ['created_at','updated_at','created_by','created_on','span']
    def __init__(self, *args, **kwargs):
        super(B2BLeadForm, self).__init__(*args, **kwargs)

        for field in [B2BLead.first_name.field_name, B2BLead.last_name.field_name, B2BLead.phone_number.field_name, B2BLead.address.field_name, B2BLead.state.field_name,
                      B2BLead.zip_code.field_name, B2BLead.comments.field_name, B2BLead.response.field_name]:
            self.fields[field].required = False
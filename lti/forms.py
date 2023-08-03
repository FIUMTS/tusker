from django import forms

class appForm(forms.Form):
	header = forms.CharField(widget=forms.Textarea())
	body = forms.CharField(widget=forms.Textarea())


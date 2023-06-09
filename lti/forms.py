from django import forms

class appForm(forms.Form):
	url = forms.URLField(label="Your web app address", required=True)
	apikey = forms.CharField(max_length=100, label="API key", disabled=True, required=False)

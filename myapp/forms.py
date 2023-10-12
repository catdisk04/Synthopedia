from django import forms

class Optimise_input(forms.Form):   
    rbs_seq = forms.CharField(label="RBS sequence")
    cds_seq = forms.CharField(label="Coding sequence")
    target_rate = forms.DecimalField(label = "Target relative expression")
    temp = forms.DecimalField(label="Temperature (°C)")
    gram = forms.ChoiceField(label="Gram stain of chassis", choices = [("1", "Positive"), ("2", "Negative")])
    rrna = forms.CharField(label = "16S rRNA sequence")
    protect = forms.CharField(label = "Sequence positions to exclude from modification", required=False, help_text="(comma separated integers - e.g. 0,1,2,17,18)")

class Predict_input(forms.Form):
    rbs_seq = forms.CharField(label="RBS sequence")
    cds_seq = forms.CharField(label="Coding sequence")
    temp = forms.DecimalField(label="Temperature (°C)")
    gram = forms.ChoiceField(label="Gram stain of chassis", choices = [("1", "Positive"), ("2", "Negative")])
    rrna = forms.CharField(label = "16S rRNA sequence")

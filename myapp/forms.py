from django import forms

class Optimise_input(forms.Form):
    rbs_seq = forms.CharField(label="RBS Sequence")
    cds_seq = forms.CharField(label="Coding Sequence")
    target_rate = forms.DecimalField(label = "Target rate")
    temp = forms.DecimalField(label="Temperature (°C)")
    gram = forms.ChoiceField(label="Gran Stain of Chassis", choices = [("1", "Positive"), ("2", "Negative")])
    rrna = forms.CharField(label = "16S rRNA Sequence")

class Predict_input(forms.Form):
    rbs_seq = forms.CharField(label="RBS Sequence")
    cds_seq = forms.CharField(label="Coding Sequence")
    temp = forms.DecimalField(label="Temperature (°C)")
    gram = forms.ChoiceField(label="Gram Stain of Chassis", choices = [("1", "Positive"), ("2", "Negative")])
    rrna = forms.CharField(label = "16S rRNA Sequence")

from django import forms
from .engine import org_choices

class Optimise_input(forms.Form):
    rbs_seq = forms.CharField(label="RBS Sequence")
    cds_seq = forms.CharField(label="Coding Sequence")
    target_rate = forms.DecimalField(label = "Target rate")
    temp = forms.DecimalField(label="Temperature (C)")
    gram = forms.ChoiceField(label="Organism", choices = ["Positive", "Negative"])
    rrna = fofrms.CharField(label = "rRNA Sequence")

class Predict_input(forms.Form):
    rbs_seq = forms.CharField(label="RBS Sequence")
    cds_seq = forms.CharField(label="Coding Sequence")
    temp = forms.DecimalField(label="Temperature (C)")
    gram = forms.ChoiceField(label="Organism", choices = ["Positive", "Negative"])

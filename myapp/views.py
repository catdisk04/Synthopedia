from django.shortcuts import render, HttpResponse
from .forms import Optimise_input, Predict_input
from . import engine

# Create your views here.
def home(request):
    return render(request, "home.html", {"name":"Name"})

def optimise(request):
    if request.method == "POST":
        form = Optimise_input(request.POST)
        if form.is_valid():
            input = form.cleaned_data
            if engine.is_valid_seq(input["rbs_seq"]):
                result = engine.optimise(input["rbs_seq"], input["target_rate"], input["temp"], input["gram"], input["cds_seq"], input["rrna"])

                return render(request, "optimise_result.html", {"form": form, "result":result})
            else:
                return render(request,"optimise.html", {"form": form, "error":"Invalid sequence"})
        else:
            print("NOT VALID")

    else:
        form = Optimise_input()
        return render(request, "optimise.html", {"form": form})

def predict(request):
    if request.method == "POST":
        form = Predict_input(request.POST)
        if form.is_valid():
            input = form.cleaned_data
            if engine.is_valid_seq(input["rbs_seq"]):
                result = engine.predict(input["rbs_seq"],  input["temp"], input["gram"], input["cds_seq"])
                return render(request, "predict_result.html", {"form": form, "result":result})
            else:
                return render(request,"predict.html", {"form": form, "error":"Invalid sequence"})
        else:
            print("NOT VALID")
    else:
        form = Predict_input()
        return render(request, "predict.html", {"form": form})
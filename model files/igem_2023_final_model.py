# -*- coding: utf-8 -*-
"""iGEM 2023 - Final Model.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1VAh9wOqU5ko0ITB6_hMlbM86_HQyj-Fg

# Environment Setup

We will require a Conda environment in order to import the `ViennaRNA` library created by [Lorenz et al. (2011)](https://doi.org/10.1186/1748-7188-6-26).
"""

# !pip install -q condacolab
# import condacolab
# condacolab.install()

"""With the Conda environment now installed, we can install the `ViennaRNA` library.

**NOTE**: Colab will crash after this install. Run the subsequent cells manually by clicking an appropriate option under the **Runtime** menu.
"""

# !conda install -c bioconda viennarna

"""# Imports"""

import RNA
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats

"""The `find_hybridization_energy` function takes in two RNA sequences and returns their hybridization energy."""

def find_hybridization_energy(sequence1, sequence2, temp):

    RNA.cvar.temperature = temp

    # First, we concatenate the two RNA sequences using the '&' symbol
    hybrid_sequence = RNA.fold_compound(f"{sequence1}&{sequence2}")

    # Finally, we use the ViennaRNA library's inbuilt mfe_dimer function to compute the hybridization energy
    structure, energy = hybrid_sequence.mfe_dimer()

    return energy

"""# Dataset for model building

We load a dataset containing mRNA sequences and their experimentally found expression levels to building our model. This dataset is from [Reis and Salis (2020)](https://doi.org/10.1021/acssynbio.0c00394 ), which contains 1014 mRNA sequences that were tested in different organisms with different reporter genes.

**NOTE**: Any datasets will have to be loaded manually every time. Google Colab does not store the files permanently.
"""

df = pd.read_csv("Dataset - Reis and Salis - 1014.csv")

len(df)

df.head()

df["Bacterial species"].value_counts()

df["Reporter"].value_counts()

"""We will have to perform the following data preprocessing tasks:

*   Convert all sequences to uppercase
*   Replace thymine with uracil in all sequences
*   Convert the expression level to a logarithmic scale
"""

df["rRNA"] = df["rRNA"].apply(lambda x: x.upper().replace("T","U"))
df["RBS"] = df["RBS"].apply(lambda x: x.upper().replace("T","U"))
df["CDS"] = df["CDS"].apply(lambda x: x.upper().replace("T","U"))

df["Mean expression"] = df["Mean expression"].apply(lambda x: np.log10(x))

"""# 16S rRNA binding

We have to understand how many nucleotides of the 16S rRNA actually bind to the RBS.
"""

def bind_rRNA(rRNA,rbs,temp):

  RNA.cvar.temperature = temp
  min_energy = 0

  for i in range(len(rbs)-len(rRNA)+1):
    energy = find_hybridization_energy(rRNA,rbs[i:i+len(rRNA)],temp)

    if energy < min_energy:
      min_energy = energy

  return abs(min_energy)

bind_rRNA = np.vectorize(bind_rRNA)

for i in range(4,10):

  df["rRNA sequence"] = df["rRNA"].apply(lambda x: x[-i:])
  df["Binding energy"] = bind_rRNA(df["rRNA sequence"],df["RBS"],df["Temperature"])
  corr = np.corrcoef(df["Mean expression"],df["Binding energy"])[0][1]
  print(f"{i} - {corr}")
  df = df.drop(["rRNA sequence","Binding energy"],axis=1)

"""We get the highest correlation with expression level when we consider the binding of the last **8 nucleotides** of the 16S rRNA. This is consistent with the findings of [Yusupova et al. (2001)](https://doi.org/10.1016/S0092-8674(01)00435-4)"""

df["rRNA"] = df["rRNA"].apply(lambda x: x[-8:])

"""# Effect of spacing

The spacing between the Shine-Dalgarno sequence and the start codon also influences the rate of translation. Any deviation from the optimal spacing will result in a lower efficiency.

[Vellanoweth and Rabinowitz (1992)](https://doi.org/10.1111/j.1365-2958.1992.tb01548.x) found that the optimal spacing differs in Gram-positive and Gram-negative bacteria. It is 9 nucleotides in Gram-positives and 7 nucleotides in Gram-negatives. They also found that Gram-positive bacteria are better at translation when the spacing is longer, but Gram-negative bacteria can tolerate shorter spacings better.

To account for the effect of spacing, we will penalise non-optimal spacing using a **Gaussian-like** distribution. We will also take into account the findings of Vellanoweth and Rabinowitz while designing this penalty term.
"""

def find_spacing(rRNA,rbs,temp,gram):

  RNA.cvar.temperature = temp
  min_energy = 0
  sd = ""
  best_spacing = 0

  for i in range(len(rbs)-len(rRNA)+1):

    energy = find_hybridization_energy(rRNA,rbs[i:i+len(rRNA)],temp)
    spacing = len(rbs[i+len(rRNA):])
    penalty = 1

    if gram == "Positive":
      opt_spacing = 9
      if spacing < opt_spacing:
        penalty = np.exp(-0.5*(((spacing - opt_spacing)**2)/1))                   # Punishing lower spacing more for Gram-positives
      elif spacing > opt_spacing:
        penalty = np.exp(-0.5*(((spacing - opt_spacing)**2)/2))
    elif gram == "Negative":
      opt_spacing = 7
      if spacing < opt_spacing:
        penalty = np.exp(-0.5*(((spacing - opt_spacing)**2)/2))
      elif spacing > opt_spacing:
        penalty = np.exp(-0.5*(((spacing - opt_spacing)**2)/1))                   # Punishing higher spacing more for Gram-negatives

    energy = energy * penalty

    if energy <= min_energy:
      min_energy = energy
      sd = rbs[i:i+len(rRNA)]
      best_spacing = spacing

  return find_hybridization_energy(rRNA,sd,temp), sd, best_spacing

find_spacing = np.vectorize(find_spacing)

df["Binding energy"], df["Shine-Dalgarno"], df["Spacing"] = find_spacing(df["rRNA"],df["RBS"],df["Temperature"],df["Gram stain"])

"""We can see that there is a good correlation between the binding energy and the expression level. Stronger binding leads to higher expression."""

plt.figure(dpi=200)
plt.scatter(df["Binding energy"],df["Mean expression"])
plt.xlabel("Binding energy")
plt.ylabel("Mean expression");

"""The most frequently occurring Shine-Dalgarno sequence appears to be `UAAGGAGG`. This is consistent with [existing literature](https://doi.org/10.1073/pnas.71.4.1342)."""

df["Shine-Dalgarno"].mode()

plt.figure(dpi=200)
au_values = df["Shine-Dalgarno"].value_counts().nlargest(5)
sns.barplot(x=au_values.index,y=au_values.values,color="blue")
plt.xlabel("Predicted Shine-Dalgarno sequence")
plt.ylabel("Value counts");

"""We can see that spacings close to the optimum give rise to higher expressions, on average."""

df.groupby("Spacing").mean(numeric_only=True)["Mean expression"].nlargest(3)

"""We can also see that extreme spacings give rise to lower expressions, on average."""

df.groupby("Spacing").mean(numeric_only=True)["Mean expression"].nsmallest(3)

plt.figure(dpi=200)
negatives = df[df["Gram stain"] == "Negative"].groupby("Spacing").mean(numeric_only=True)
sns.barplot(x=negatives.index,y="Mean expression",data=negatives,color="blue")
plt.title("Effect of spacing in Gram-negatives")
plt.axvline(6,c="r",ls="--");

plt.figure(dpi=200)
positives = df[df["Gram stain"] == "Positive"].groupby("Spacing").mean(numeric_only=True)
sns.barplot(x=positives.index,y="Mean expression",data=positives,color="blue")
plt.title("Effect of spacing in Gram-positives")
plt.axvline(5,c="r",ls="--");

"""However, when the spacing is optimum, other factors can still play a role in determining the overall translation efficiency. This can be seen from the range of expression levels even with optimal spacing."""

plt.figure(dpi=200)
plt.scatter(df["Spacing"],df["Mean expression"])
plt.xlabel("Spacing")
plt.ylabel("Mean expression")
plt.axvline(7,c="r",ls="--")
plt.axvline(9,c="r",ls="--");

"""# Effect of S1 ribosomal protein

[Komarova et al. (2005)](https://doi.org/10.1128/jb.187.4.1344-1349.2005) found that the S1 protein present in the ribosome's 30S subunit interacts with A/U-rich sequences upstream of the Shine-Dalgarno site. This interaction is believed to protect the mRNA from degradation by RNases, which also use A/U-rich sequences as recognition sites. The insertion of A/U-rich elements upstream of the Shine-Dalgarno sequence enhances translation efficiency.

X-ray crystallographic studies by [Sengupta et al. (2001)](https://doi.org/10.1073%2Fpnas.211266898) found that the S1 protein interacts with 11 nucleotides upstream of the Shine-Dalgarno sequence.

To quantify this interaction, we simply calculate the number of adenine and uracil nucleotides in the mRNA's putative region of interaction with the S1 protein.
"""

def find_au_score(rbs,sd):

    sd_loc = rbs.index(sd)
    upstream = rbs[sd_loc-11 : sd_loc]

    au_score = upstream.count("A") + upstream.count("U")

    if len(upstream) == 0:
      return 0
    else:
      return au_score / len(upstream)

find_au_score = np.vectorize(find_au_score)

df["AU score"] = find_au_score(df["RBS"],df["Shine-Dalgarno"])

"""We can see that mRNAs with higher A/U scores tend to have higher expression levels, on average."""

plt.figure(dpi=200)
au_data = df.groupby("AU score").mean(numeric_only=True)
slope, intercept, r_value, pv, se = stats.linregress(au_data.index, au_data["Mean expression"])
ax = sns.regplot(x=au_data.index,y="Mean expression",data=au_data,ci=None,line_kws={'label':f"y = {slope:.3f}x+{intercept:.3f}\nR\u00b2 = {r_value:.3f}"})
plt.legend()
plt.title("Mean expressions grouped by A/U score")
plt.xlabel("A/U score");

"""# Regional folding of the mRNA

The region of the mRNA containing the RBS can transiently fold and unfold. The ribosome can only bind to the RBS if it is accessible. This means that the region surrounding the RBS should be free of secondary structures, or if secondary structures are present, they should be easily removable (i.e., lesser work required to unfold them).

[Hüttenhofer and Noller (1994)](https://doi.org/10.1002%2Fj.1460-2075.1994.tb06700.x) found that the 30S subunit interacts with 54-57 nucleotides of the mRNA. We will consider this region, centered around the start codon, while determining its accessibility. We crudely quantify the accessibility by considering the number of paired and unpaired nucleotides in the secondary structure of the region under consideration.
"""

def find_accessibility_score(rbs,cds,sd,temp):

  RNA.cvar.temperature = temp

  sd_loc = rbs.index(sd)

  upstream = rbs[-27:]
  downstream = cds[:54-len(upstream)]

  structure, fold_energy = RNA.fold(upstream + downstream)

  loop_count = structure.count(".")                                               # Number of unpaired nucleotides
  stack_count = structure.count("(") + structure.count(")")                       # Number of paired nucleotides

  accessibility_score = loop_count / (loop_count + stack_count)

  return structure, accessibility_score, fold_energy

find_accessibility_score = np.vectorize(find_accessibility_score)

df["Structure"], df["Accessibility score"], df["Folding energy"] = find_accessibility_score(df["RBS"],df["CDS"],df["Shine-Dalgarno"],df["Temperature"])

"""We can see that a higher accessibility score leads to higher expression levels, on average."""

plt.figure(dpi=200)
access_data = df.groupby("Accessibility score").mean(numeric_only=True)
slope, intercept, r_value, pv, se = stats.linregress(access_data.index, access_data["Mean expression"])
ax = sns.regplot(x=access_data.index,y="Mean expression",data=access_data,ci=None,line_kws={'label':f"y = {slope:.3f}x+{intercept:.3f}\nR\u00b2 = {r_value:.3f}"})
plt.legend()
plt.title("Mean expressions grouped by accessibility score")
plt.xlabel("Accessibility score");

"""We can also see that having a higher folding energy (i.e., lesser work required for unfolding) also leads to higher expression levels."""

plt.figure(dpi=200)
plt.scatter(df["Folding energy"],df["Mean expression"])
plt.xlabel("Folding energy")
plt.ylabel("Mean expression");

"""# Standby sites

If the RBS is transiently folded, the ribosome may bind to standby sites upstream of the Shine-Dalgarno sequence (See: [de Smit and van Duin (2003)](https://doi.org/10.1016/S0022-2836(03)00809-X)). This site has to be easily accessible to the ribosome. Thus, it should have minimal secondary structure formation. The standby site should not be too far from the Shine-Dalgarno sequence as well.

We define the accessibility of the standby site by considering the number of paired and unpaired nucleotides in the standby site. We penalise large gaps between the standby site and the Shine-Dalgarno sequence by dividing the accessibility by the length of the gap.
"""

def find_standby_score(rbs,sd,structure):

  sd_loc = rbs.index(sd)

  upstream = rbs[:sd_loc]
  upstream_structure = structure[:sd_loc]
  rRNA_length = 8

  if len(upstream_structure) != 0:

    upstream = upstream[::-1]
    upstream_structure = upstream_structure[::-1]

    best_accessibility = 0

    for i in range(len(upstream)-rRNA_length+1):

      gap = i+rRNA_length
      loop_count = upstream_structure[i:i+rRNA_length].count(".")
      stack_count = upstream_structure[i:i+rRNA_length].count("(") + upstream_structure[i:i+rRNA_length].count(")")
      accessibility = loop_count / rRNA_length
      penalised_accessibility = accessibility / gap

      if penalised_accessibility > best_accessibility:
        best_accessibility = accessibility

    return best_accessibility

  else:

    return 0

find_standby_score = np.vectorize(find_standby_score)

df["Standby accessibility"] = find_standby_score(df["RBS"],df["Shine-Dalgarno"],df["Structure"])

"""We can see that more accessible standby sites have a higher expression level than less accessible standby sites.

"""

plt.figure(dpi=200)
access_data = df.groupby("Standby accessibility").mean(numeric_only=True)
slope, intercept, r_value, pv, se = stats.linregress(access_data.index, access_data["Mean expression"])
ax = sns.regplot(x=access_data.index,y="Mean expression",data=access_data,ci=None,line_kws={'label':f"y = {slope:.3f}x+{intercept:.3f}\nR\u00b2 = {r_value:.3f}"})
plt.legend()
plt.title("Mean expressions grouped by standby accessibility")
plt.xlabel("Standby accessibility");

"""# Effect of start codon

The start codon in the coding sequence can also influence translation efficiency. [Hecht et al. (2017)](https://doi.org/10.1093%2Fnar%2Fgkx070) characterized the strengths of the 64 possible start codons. Using their experimental data, we develop a scoring system for the different start codons.
"""

codon_scores = {"AGC":0,"CCG":0.78,"CAG":0.95,"UGC":1.01,"CUC":1.1,"UCC":1.1,"CCC":1.17,"UAG":1.19,"CGG":1.2,"CUU":1.21,"CCU":1.26,"UUC":1.29,"CCA":1.3,"UAC":1.3,"CGC":1.31,"UCU":1.32,"ACC":1.32,"ACA":1.33,"CGU":1.33,"GCC":1.33,"CUA":1.34,"AAC":1.37,"CAC":1.41,"UCA":1.41,"AAA":1.43,"GCU":1.45,"AGU":1.46,"UAA":1.47,"GGC":1.48,"AGA":1.51,"UUU":1.54,"GAC":1.54,"AAG":1.56,"ACU":1.56,"UGA":1.56,"UGU":1.59,"CAA":1.59,"GUC":1.61,"GCA":1.64,"UGG":1.66,"CGA":1.69,"AGG":1.71,"GGA":1.71,"GGU":1.71,"GAG":1.72,"UUA":1.72,"UCG":1.78,"GGG":1.79,"GCG":1.84,"ACG":1.88,"GAU":1.92,"AAU":1.93,"GAA":2.12,"GUU":2.1,"GUA":2.11,"UAU":2.16,"CAU":2.17,"AUC":2.41,"AUU":2.57,"CUG":2.63,"AUA":2.73,"UUG":4.18,"GUG":4.22,"AUG":4.3}

codons = pd.DataFrame(codon_scores,index=[0]).transpose()
codons.columns = ["Codon Score"]
codons

def find_codon_score(cds):

  codon = cds[:3]
  codon_score = codon_scores[codon]

  return codon_score

df["Codon score"] = df["CDS"].apply(find_codon_score)

"""We can see that when the codon score is lesser than 4, the expression level reduces."""

plt.figure(dpi=200)
plt.scatter(df["Codon score"],df["Mean expression"])
plt.xlabel("Codon score")
plt.ylabel("Mean expression");

plt.figure(dpi=200)
access_data = df.groupby("Codon score").mean(numeric_only=True)
slope, intercept, r_value, pv, se = stats.linregress(access_data.index, access_data["Mean expression"])
ax = sns.regplot(x=access_data.index,y="Mean expression",data=access_data,ci=None,line_kws={'label':f"y = {slope:.3f}x+{intercept:.3f}\nR\u00b2 = {r_value:.3f}"})
plt.legend()
plt.title("Mean expressions grouped by codon score")
plt.xlabel("Codon score");

"""# Gram stain

To distinguish between Gram negatives and positives, we add an additional column where negatives are denoted by 0 and positives are denoted by 1.
"""

df["Gram stain numeric"] = df["Gram stain"].apply(lambda x: 0 if x=="Negative" else 1)

"""# Model training

First, we split the data into features and labels.
"""

X = df[["Binding energy",
        "Spacing",
        "AU score",
        "Accessibility score",
        "Folding energy",
        "Standby accessibility",
        "Codon score",
        "Gram stain numeric"]]
y = df[["Mean expression",
        "RBS Calculator v1.0 prediction",
        "RBS Calculator v1.1 prediction",
        "RBS Calculator v2.0 prediction",
        "RBS Calculator v2.1 prediction",
        "RBS Designer prediction",
        "UTR Designer prediction",
        "EMOPEC prediction"]]

"""We train Random Forest Regressors with different hyperparameters using grid search cross validation. We then compare the performance of our "best" model with the RBS Calculator v2.1 for different train-test splits created by random seeds."""

from sklearn.model_selection import train_test_split

from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import GridSearchCV

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.01, random_state=23)

param_grid = {
    'max_depth': [80, 90, 100, 110],
    'max_features': [2, 3],
    'min_samples_leaf': [3, 4, 5],
    'min_samples_split': [8, 10, 12],
    'n_estimators': [50, 100, 200, 300, 1000]
}

rf = RandomForestRegressor(random_state=23)

grid_search = GridSearchCV(estimator = rf, param_grid = param_grid, cv = 3, n_jobs = -1, verbose = 2)

grid_search.fit(X_train,y_train["Mean expression"])

grid_search.best_estimator_

model = RandomForestRegressor(max_depth=80, max_features=3, min_samples_leaf=3, min_samples_split=8, n_estimators=50, random_state=23)

seed_range = range(1000)

model_perf = []
rbs_calc_v1_0_perf = []
rbs_calc_v1_1_perf = []
rbs_calc_v2_0_perf = []
rbs_calc_v2_1_perf = []
rbs_designer_perf = []
utr_designer_perf = []
emopec_perf = []

for seed in seed_range:
  X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.01, random_state=seed)
  model.fit(X_train,y_train["Mean expression"])
  predictions = model.predict(X_test)
  model_perf.append(np.corrcoef(y_test["Mean expression"],predictions)[0][1]**2)
  rbs_calc_v1_0_perf.append(np.corrcoef(y_test["Mean expression"].apply(lambda x: 10**x),y_test["RBS Calculator v1.0 prediction"])[0][1]**2)
  rbs_calc_v1_1_perf.append(np.corrcoef(y_test["Mean expression"].apply(lambda x: 10**x),y_test["RBS Calculator v1.1 prediction"])[0][1]**2)
  rbs_calc_v2_0_perf.append(np.corrcoef(y_test["Mean expression"].apply(lambda x: 10**x),y_test["RBS Calculator v2.0 prediction"])[0][1]**2)
  rbs_calc_v2_1_perf.append(np.corrcoef(y_test["Mean expression"].apply(lambda x: 10**x),y_test["RBS Calculator v2.1 prediction"])[0][1]**2)
  rbs_designer_perf.append(np.corrcoef(y_test["Mean expression"].apply(lambda x: 10**x),y_test["RBS Designer prediction"])[0][1]**2)
  utr_designer_perf.append(np.corrcoef(y_test["Mean expression"].apply(lambda x: 10**x),y_test["UTR Designer prediction"])[0][1]**2)
  emopec_perf.append(np.corrcoef(y_test["Mean expression"].apply(lambda x: 10**x),y_test["EMOPEC prediction"])[0][1]**2)

"""To prevent getting errors from correlations that are not a number, we convert the NaN correlations to 0."""

rbs_calc_v1_0_perf_new = [x if x % 1 == x else 0 for x in rbs_calc_v1_0_perf]
rbs_calc_v1_1_perf_new = [x if x % 1 == x else 0 for x in rbs_calc_v1_1_perf]
rbs_calc_v2_0_perf_new = [x if x % 1 == x else 0 for x in rbs_calc_v2_0_perf]
rbs_designer_perf_new = [x if x % 1 == x else 0 for x in rbs_designer_perf]
utr_designer_perf_new = [x if x % 1 == x else 0 for x in utr_designer_perf]
emopec_perf_new = [x if x % 1 == x else 0 for x in emopec_perf]

"""We can now compare performances."""

print(f"Model - {np.mean(model_perf)}")
print(f"RBS Calculator v1.0 - {np.mean(rbs_calc_v1_0_perf_new)}")
print(f"RBS Calculator v1.1 - {np.mean(rbs_calc_v1_1_perf_new)}")
print(f"RBS Calculator v2.0 - {np.mean(rbs_calc_v2_0_perf_new)}")
print(f"RBS Calculator v2.1 - {np.mean(rbs_calc_v2_1_perf)}")
print(f"RBS Designer - {np.mean(rbs_designer_perf_new)}")
print(f"UTR Designer - {np.mean(utr_designer_perf_new)}")
print(f"EMOPEC - {np.mean(emopec_perf_new)}")

"""To get the best out of our model, we will retrain it on the whole dataset."""

final_model = RandomForestRegressor(max_depth=80, max_features=3, min_samples_leaf=3, min_samples_split=8, n_estimators=50, random_state=23)

final_model.fit(X, y["Mean expression"]);

"""We can also examine the features that the model deemed were important."""

for i in range(len(X.columns)):
  print(f"{model.feature_importances_[i]} - {X.columns[i]}")

"""`Binding energy` and `Folding energy` seem to be the most important factors while determining the expression level.

We can now test it on another dataset to get a true measure of its performance.

# Further testing

We will test our model on a dataset of 16779 mRNA sequences (from [Reis and Salis (2020)](https://doi.org/10.1021/acssynbio.0c00394)) characterized by FlowSeq. The RBS Calculator achieves an R² of 0.17 on this dataset.
"""

flowseq = pd.read_csv("Dataset - Reis and Salis - 16779.csv")

len(flowseq)

flowseq["rRNA"] = flowseq["rRNA"].apply(lambda x: x.upper().replace("T","U"))
flowseq["RBS"] = flowseq["RBS"].apply(lambda x: x.upper().replace("T","U"))
flowseq["CDS"] = flowseq["CDS"].apply(lambda x: x.upper().replace("T","U"))
flowseq["rRNA"] = flowseq["rRNA"].apply(lambda x: x[-8:])
flowseq["Mean expression"] = flowseq["Mean expression"].apply(lambda x: np.log10(x))

flowseq["Binding energy"], flowseq["Shine-Dalgarno"], flowseq["Spacing"] = find_spacing(flowseq["rRNA"],flowseq["RBS"],flowseq["Temperature"],flowseq["Gram stain"])
flowseq["AU score"] = find_au_score(flowseq["RBS"],flowseq["Shine-Dalgarno"])
flowseq["Structure"], flowseq["Accessibility score"], flowseq["Folding energy"] = find_accessibility_score(flowseq["RBS"],flowseq["CDS"],flowseq["Shine-Dalgarno"],flowseq["Temperature"])
flowseq["Standby accessibility"] = find_standby_score(flowseq["RBS"],flowseq["Shine-Dalgarno"],flowseq["Structure"])
flowseq["Codon score"] = flowseq["CDS"].apply(find_codon_score)
flowseq["Gram stain numeric"] = flowseq["Gram stain"].apply(lambda x: 0 if x=="Negative" else 1)

X = flowseq[["Binding energy","Spacing","AU score","Accessibility score","Folding energy","Standby accessibility","Codon score","Gram stain numeric"]]
y = flowseq["Mean expression"]
p = final_model.predict(X)
np.corrcoef(y,p)[0][1]**2

"""The RBS Calculator v2.1 has a correlation of 0.167 on this dataset.

# Saving the model

We save the trained model for later use.
"""

import joblib

joblib.dump(final_model,"iGEM IITM 2023 - Final Model.joblib")
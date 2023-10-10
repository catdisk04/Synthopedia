#!/usr/bin/env python
# coding: utf-8

# In[1]:


#get_ipython().system('pip install -q condacolab')
#import condacolab
#condacolab.install()


# In[1]:


# get_ipython().system('conda install -c bioconda viennarna')


# In[2]:


import RNA
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import joblib


# In[3]:


def find_hybridization_energy(sequence1, sequence2, temp):

    RNA.cvar.temperature = temp

    # First, we concatenate the two RNA sequences using the '&' symbol
    hybrid_sequence = RNA.fold_compound(f"{sequence1}&{sequence2}")

    # Finally, we use the ViennaRNA library's inbuilt mfe_dimer function to compute the hybridization energy
    structure, energy = hybrid_sequence.mfe_dimer()

    return energy


# In[4]:


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


# In[5]:


def find_au_score(rbs,sd):

    sd_loc = rbs.index(sd)
    upstream = rbs[sd_loc-11 : sd_loc]

    au_score = upstream.count("A") + upstream.count("U")

    if len(upstream) == 0:
      return 0
    else:
      return au_score / len(upstream)


# In[6]:


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


# In[7]:


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


# In[8]:


codon_scores = {"AGC":0,"CCG":0.78,"CAG":0.95,"UGC":1.01,"CUC":1.1,"UCC":1.1,"CCC":1.17,"UAG":1.19,"CGG":1.2,"CUU":1.21,"CCU":1.26,"UUC":1.29,"CCA":1.3,"UAC":1.3,"CGC":1.31,"UCU":1.32,"ACC":1.32,"ACA":1.33,"CGU":1.33,"GCC":1.33,"CUA":1.34,"AAC":1.37,"CAC":1.41,"UCA":1.41,"AAA":1.43,"GCU":1.45,"AGU":1.46,"UAA":1.47,"GGC":1.48,"AGA":1.51,"UUU":1.54,"GAC":1.54,"AAG":1.56,"ACU":1.56,"UGA":1.56,"UGU":1.59,"CAA":1.59,"GUC":1.61,"GCA":1.64,"UGG":1.66,"CGA":1.69,"AGG":1.71,"GGA":1.71,"GGU":1.71,"GAG":1.72,"UUA":1.72,"UCG":1.78,"GGG":1.79,"GCG":1.84,"ACG":1.88,"GAU":1.92,"AAU":1.93,"GAA":2.02,"GUU":2.1,"GUA":2.11,"UAU":2.16,"CAU":2.17,"AUC":2.41,"AUU":2.57,"CUG":2.63,"AUA":2.73,"UUG":4.18,"GUG":4.22,"AUG":4.3}


# In[9]:


def find_codon_score(cds):

  codon = cds[:3]
  codon_score = codon_scores[codon]

  return codon_score


# In[10]:


model = joblib.load("iGEM IITM 2023 - Final Model.joblib")


# In[15]:


def find_tir(gram_stain,temperature,rRNA,RBS,CDS):

  rRNA = rRNA.upper().replace("T","U")
  RBS = RBS.upper().replace("T","U")
  CDS = CDS.upper().replace("T","U")
  rRNA = rRNA[-8:]

  binding_energy, shine_dalgarno, spacing = find_spacing(rRNA,RBS,temperature,gram_stain)
  au_score = find_au_score(RBS,shine_dalgarno)
  structure, accessibility_score, folding_energy = find_accessibility_score(RBS,CDS,shine_dalgarno,temperature)
  standby_accessibility = find_standby_score(RBS,shine_dalgarno,structure)
  codon_score = find_codon_score(CDS)

  gram_stain_numeric = 1
  if gram_stain == "Negative":
    gram_stain_numeric = 0

  features = np.array([binding_energy, spacing, au_score, accessibility_score, folding_energy, standby_accessibility, codon_score,gram_stain_numeric]).reshape(1,-1)
  df = pd.DataFrame(features)
  df.columns = ["Binding energy","Spacing","AU score","Accessibility score","Folding energy","Standby accessibility","Codon score","Gram stain numeric"]

  tir = model.predict(df)[0]

  return tir


# In[16]:

if __name__ == "__main__":
  gram = "Negative"
  temp = 37
  rRNA = "CCUCCUUA"
  rbs = "UUCUAGAGUGCAUAAGGAGUGCUCG"
  cds = "AUGUCCAGAUUAGAUAAAAGUAAAGUGAUGGCGAGCUCUGAAGACGUUAUCAAAGAGUUCAUGCGUUUCAAAGUUCGUAUGGAAGGUUCCGUUAACGGUCACGAGUUCGAAAUCGAAGGUGAAGGUGAAGGUCGUCCGUACGAAGGUACCCAGACCGCUAAACUGAAAGUUACCAAAGGUGGUCCGCUGCCGUUCGCUUGGGACAUCCUGUCCCCGCAGUUCCAGUACGGUUCCAAAGCUUACGUUAAACACCCGGCUGACAU"
  find_tir(gram, temp, rRNA, rbs, cds)


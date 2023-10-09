#!/usr/bin/env python
# coding: utf-8

# In[6]:


# get_ipython().system('pip install -q condacolab')
# import condacolab
# condacolab.install()


# In[1]:


# get_ipython().system('conda install -c bioconda viennarna')


# In[2]:


import RNA
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import joblib
import random


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


# In[11]:


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


# In[25]:


# Functions to mutate the RBS sequence

def mutate_base(base, mutation_rate):
    bases = "ACGU"
    return random.choice(bases) if random.random() < mutation_rate else base

def mutate_rbs(rbs, mutation_rate = 0.1, positions_to_protect = []):
    bases = "ACGU"
    mutated_rbs = []
    for idx, base in enumerate(rbs):
        if idx in positions_to_protect:
            mutated_rbs.append(base)    # Keep the base unchanged for the Shine-Dalgarno Sequence
        else:
            mutated_rbs.append(mutate_base(base, mutation_rate)) # Mutate the rest

    return ''.join(mutated_rbs)

def single_point_crossover(mutated_rbs_list, i1, i2, i3, i4):
    # Perform single-point crossover
    rbs1 = mutated_rbs_list[i1]
    rbs2 = mutated_rbs_list[i2]
    rbs3 = mutated_rbs_list[i3]
    rbs4 = mutated_rbs_list[i4]

    crossover_point = random.randint(1, len(rbs1) - 1)
    # Exchanging the RBS at a random crossover point
    child1 = rbs1[:crossover_point] + rbs2[crossover_point:]
    child2 = rbs2[:crossover_point] + rbs1[crossover_point:]
    child3 = rbs3[:crossover_point] + rbs4[crossover_point:]
    child4 = rbs4[:crossover_point] + rbs3[crossover_point:]
    return child1, child2, child3, child4

# RBS optimization
def optimize_rbs(desired_initiation_rate, gram_stain, temperature, rRNA, RBS, CDS, generations=100, population_size=50, mutation_rate=0.1):
    rbs_sequence = RBS.upper().replace("T","U")
    if rbs_sequence == "":
      rbs_sequence = "".join(random.choices(["A","C","G","U"],k=27))
    CDS = CDS.upper().replace("T","U")
    consecutive_same_best_rate = 0
    best_RBS_sequences = []
    best_RBS_rates = []

    for generation in range(generations):
        # Calculate initiation rate for the current RBS sequence
        current_rate = find_tir(gram_stain, temperature, rRNA, rbs_sequence, CDS)
        best_RBS_sequences.append(rbs_sequence)
        best_RBS_rates.append(current_rate)
        print(f"Generation {generation+1}, Current RBS: {rbs_sequence}, Initiation Rate: {current_rate}")

        if abs(current_rate - desired_initiation_rate) < 1e-4: # Choosing the accuracy we require
            print("Optimization successful!")
            break
        # Generate a new mutated RBS sequence
        best_rate = 500 # Setting an arbitrary high best rate
        rbs_sequence_1 = rbs_sequence
        mutated_rbs_list = [] # Creating a list for the mutated RBS

        for i in range(population_size):
            new_rbs = mutate_rbs(rbs_sequence, mutation_rate)
            mutated_rbs_list.append(new_rbs)

        # Perform crossover and add children to the population
        for _ in range(population_size // 2):
            i1, i2, i3, i4 = random.sample(range(population_size), 4)  # Choose 4 distinct random parents
            child1, child2, child3, child4 = single_point_crossover(mutated_rbs_list, i1, i2, i3, i4)
            mutated_rbs_list.extend([child1, child2, child3, child4])

        new_rates = []
        for i in range(len(mutated_rbs_list)):
            new_rbs = mutated_rbs_list[i]
            new_rate = find_tir(gram_stain, temperature, rRNA, new_rbs, CDS)
            new_rates.append(new_rate) # List for the rates of the mutated sequences

        # Replace the current RBS sequence with the mutated one if it leads to a better initiation rate
        for i in range(len(mutated_rbs_list)):
            if abs(new_rates[i] - desired_initiation_rate) < abs(current_rate - desired_initiation_rate):
                if abs(new_rates[i] - desired_initiation_rate) < abs(best_rate - desired_initiation_rate):
                    best_rate = new_rates[i]
                    rbs_sequence_1 = mutated_rbs_list[i]

        if best_rate == 500: # If the same rate is repeated multiple times, the best rate is not updated
            consecutive_same_best_rate += 1
        else:
            consecutive_same_best_rate = 0

        if consecutive_same_best_rate == 4:
            if abs(current_rate - desired_initiation_rate) > 0.01:
                print("Retrying for a better result")
                rbs_sequence_1 = RBS
            else:
                print("Optimization successful!")
                break

        rbs_sequence = rbs_sequence_1  # Update the current RBS sequence

    deviations = [abs(rate-desired_initiation_rate) for rate in best_RBS_rates]
    best_RBS_rate = best_RBS_rates[deviations.index(min(deviations))]
    best_RBS_sequence = best_RBS_sequences[deviations.index(min(deviations))]

    return best_RBS_sequence, best_RBS_rate


# In[26]:


gram_stain = "Negative"
temperature = 37
rRNA = "CCUCCUUA"
RBS = "UUCUAGAGUGCAUAAGGAGUGCUCG"
CDS = "AUGUCCAGAUUAGAUAAAAGUAAAGUGAUGGCGAGCUCUGAAGACGUUAUCAAAGAGUUCAUGCGUUUCAAAGUUCGUAUGGAAGGUUCCGUUAACGGUCACGAGUUCGAAAUCGAAGGUGAAGGUGAAGGUCGUCCGUACGAAGGUACCCAGACCGCUAAACUGAAAGUUACCAAAGGUGGUCCGCUGCCGUUCGCUUGGGACAUCCUGUCCCCGCAGUUCCAGUACGGUUCCAAAGCUUACGUUAAACACCCGGCUGACAU"
desired_initiation_rate = 3
optimized_rbs, optimized_rate = optimize_rbs(desired_initiation_rate, gram_stain, temperature, rRNA, RBS, CDS)
print(f"\nOptimized RBS: {optimized_rbs}")
print(f"Optimized RBS rate: {optimized_rate}")


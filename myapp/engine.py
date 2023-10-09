import Optimise, Predict

organism_choices = ["E.coli", "L.lactis"]

# org_choices = []
# for i in organism_choices.keys:
#     org_choices.append((i, i))

def optimise(rbs_seq, target, temp, gram, cds_seq, rrna):
    optimized_rbs, optimized_rate = Optimise.optimize_rbs(target, gram, temp, rrna, rbs_seq, cds_seq)
    return {"result_seq": str(optimized_rbs), "achieved_rate": str(optimized_rate)}

def predict(rbs_seq,temp, gram, cds_seq):
    result = Predict.find_tir(gram, temp, rRNA, rbs, cds)
    return {"result_rate": result}

def is_valid_seq(rbs_seq):
    return True
from optimise import *
from predict import *
# organism_choices = ["E.coli", "L.lactis"]

# org_choices = []s
# for i in organism_choices.keys:
#     org_choices.append((i, i))

def optimise(rbs_seq, target, temp, gram, cds_seq, rrna, protect):
    optimized_rbs, optimized_rate = optimize_rbs(float(target), gram, float(temp), rrna, rbs_seq, cds_seq, protect)
    return {"result_seq": str(optimized_rbs), "achieved_rate": str(optimized_rate)}
    # return {"result_seq": "AAAAAA", "achieved_rate": "10"}

def predict(rbs_seq,temp, gram, cds_seq, rrna):
    # print("NEW INPUT")
    # print("rbs_seq, temp, gram, cds_seq, rrna,")
    # print(rbs_seq, temp, gram, cds_seq, rrna, sep="\n")
    result = find_tir(gram, float(temp), rrna, rbs_seq, cds_seq)
    return {"result_rate": result}
    # return {"result_rate": "10"}

def is_valid_seq(rbs_seq):
    return True
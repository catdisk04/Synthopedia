organism_choices = ["E.coli", "L.lactis"]

org_choices = []
for i in organism_choices:
    org_choices.append((i, i))

def optimise(rbs_seq, target, temp, organism):
    return {"result_seq": "AAAA", "achieved_rate": 10}

def predict(rbs_seq,temp, organism):
    return {"result_rate": 10}

def is_valid_seq(rbs_seq):
    return True
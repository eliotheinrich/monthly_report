import dill as pkl

with open("groups.pkl", "rb") as f:
    groups = pkl.load(f)

print(groups.to_string())
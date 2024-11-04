import dill as pkl

with open("users.pkl", "rb") as f:
    users = pkl.load(f)

print(users.to_string())
print(users)
t = "Денис Б dz-1 ans-1: гроб".split()
d = {"fio": t[0] + " " + t[1], "dz": t[2].split("-")[-1], "ans": t[3].split("-")[-1], "cur_ans": t[-1]}
print(d)
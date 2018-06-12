f = open("main.css", "r")
si = f.readlines()
f.close()

s = ""

for i in si:
	was_ch = False
	for j in i:
		if j == "	" or j == "\r" or j == "\n" or (j == " " and not was_ch):
			pass
		else:
			was_ch = True
			s += j

op = False
pr = False

cn = ""
pn = ""
vn = ""

code = []

obj = [None, []]
for ch in s:
	if ch == '{':
		op = True
		obj[0] = cn
		cn = ""
	elif ch == '}':
		op = False
		code.append(obj)
		obj = [None, []]
	elif ch == ":" and op:
		pr = True
	elif ch == ";" and op:
		pr = False
		obj[1].append([pn, vn])
		pn = ""
		vn = ""
	else:
		if not op:
			cn += ch
		elif not pr:
			pn += ch
		else:
			vn += ch

for i in range(len(code)):
	code[i][1].sort()

d = {}

for i in range(len(code)):
	key = str(code[i][1])
	value = code[i][0]
	if key in d:
		d[key].append(value)
	else:
		d[key] = [value]

for i in d:
	if len(d[i]) > 1:
		for j in d[i]:
			print(j)
		print("\n")

#f = open("new_main.css", "w")
#f.write(str(d))
#f.close()
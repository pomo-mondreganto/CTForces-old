def file2code(filename):

	f = open(filename, "r")
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

	return code

def code2file(filename, code):
	f = open(filename, "w")
	for i in code:
		f.write(i[0] + " {\n")
		for j in i[1]:
			f.write("	" + j[0] + ":" + j[1] + ";\n")
		f.write("}\n\n")
	f.close()

code = file2code("cp.css")

for i in code:
	for j in i[1]:
		if j[1][-2:] == "vw":
			num = float(j[1][1:-2])
			num /= 1.2
			j[1] = " " + str(num) + "vw"


code2file("main.css", code)

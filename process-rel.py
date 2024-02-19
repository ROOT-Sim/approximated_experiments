import sys
import matplotlib.pyplot as plt
import numpy

f = open(sys.argv[1])

dataset = {}

min_ts = float('inf')
max_ts = 0

for line in f.readlines():
	if "checkpoint" in line: continue
	line = line.strip()
	line = line.split(',')
	lp = int(line[0])
	ts = float(line[2])
	pr = float(line[3])
	abs_str = float(line[4])
	rel_str = float(line[5])
	er = float('inf')
	if pr != 0:	er = (pr-rel_str)#/pr
	if pr == er: er = 0
	if lp not in dataset: dataset[lp] = {"x":[], "y":[]}
	dataset[lp]["x"] += [ts]
	dataset[lp]["y"] += [abs(er)]
	min_ts = min(min_ts, ts)
	max_ts = max(max_ts, ts)

r = sys.argv[1].replace(".txt", "-").split("/")[-1]

plt.figure(figsize=(5,4))
plt.xlabel("virtual time")
plt.ylabel("absolute error")

#plt.ylim(0, 10)
for lp in dataset:
	plt.plot(dataset[lp]["x"], dataset[lp]["y"])
plt.savefig(f"{r}trace-abs-s2.pdf")

plt.clf()


f = open(sys.argv[1])

dataset = {}

min_ts = float('inf')
max_ts = 0

for line in f.readlines():
	if "checkpoint" in line: continue
	line = line.strip()
	line = line.split(',')
	lp = int(line[0])
	ts = float(line[2])
	pr = float(line[3])
	abs_str = float(line[4])
	rel_str = float(line[5])
	er = float('inf')
	if pr != 0:	er = (pr-rel_str)/pr
	if pr == 0: er = 0.0
	if abs(er) > 0.05: print(line, abs(er))
	if lp not in dataset: dataset[lp] = {"x":[], "y":[]}
	dataset[lp]["x"] += [ts]
	dataset[lp]["y"] += [abs(er)*100]
	min_ts = min(min_ts, ts)
	max_ts = max(max_ts, ts)

r = sys.argv[1].replace(".txt", "-").split("/")[-1]

plt.figure(figsize=(5,4))
plt.xlabel("virtual time")
plt.ylabel("relative error (%)")

for lp in dataset:
	plt.plot(dataset[lp]["x"], dataset[lp]["y"])
plt.savefig(f"{r}trace-rel-s2.pdf")


plt.clf()


f = open(sys.argv[1])

dataset = {}

min_ts = float('inf')
max_ts = 0


mean = 0
if "0_1_"   in sys.argv[1]: mean = 0.5
if "0_1pI_" in sys.argv[1]: mean = 1.0
if "1_1pI_" in sys.argv[1]: mean = 2.0
if "1_1pC_" in sys.argv[1]: mean = 1.5

for line in f.readlines():
	if "checkpoint" in line: continue
	line = line.strip()
	line = line.split(',')
	lp = int(line[0])
	ts = float(line[2])
	pr = float(line[3])
	abs_str = float(line[4])
	rel_str = float(line[5])
	er = float('inf')
	if pr != 0:	er = (pr-mean)/pr
	if pr == 0 or pr == abs_str: er = 0.0
	if lp not in dataset: dataset[lp] = {"x":[], "y":[]}
	dataset[lp]["x"] += [ts]
	dataset[lp]["y"] += [abs(er)*100]
	min_ts = min(min_ts, ts)
	max_ts = max(max_ts, ts)

r = sys.argv[1].replace(".txt", "-").split("/")[-1]

plt.figure(figsize=(5,4))
plt.xlabel("virtual time")
plt.ylabel("relative error (%)")

for lp in dataset:
	plt.plot(dataset[lp]["x"], dataset[lp]["y"])
plt.savefig(f"{r}trace-rel-ba.pdf")



plt.clf()


f = open(sys.argv[1])

dataset = {}

min_ts = float('inf')
max_ts = 0

mean = 0
if "0_1_"   in sys.argv[1]: mean = 0.5
if "0_1pI_" in sys.argv[1]: mean = 1.0
if "1_1pI_" in sys.argv[1]: mean = 2.0
if "1_1pC_" in sys.argv[1]: mean = 1.5

for line in f.readlines():
	if "checkpoint" in line: continue
	line = line.strip()
	line = line.split(',')
	lp = int(line[0])
	ts = float(line[2])
	pr = float(line[3])
	abs_str = float(line[4])
	rel_str = float(line[5])
	er = float('inf')
	if pr != 0:	er = (pr-mean)
	if pr == 0 or pr == abs_str: er = 0.0
	if lp not in dataset: dataset[lp] = {"x":[], "y":[]}
	dataset[lp]["x"] += [ts]
	dataset[lp]["y"] += [abs(er)]
	min_ts = min(min_ts, ts)
	max_ts = max(max_ts, ts)

plt.figure(figsize=(5,4))
plt.xlabel("virtual time")
plt.ylabel("absolute error")
r = sys.argv[1].replace(".txt", "-").split("/")[-1]

for lp in dataset:
	plt.plot(dataset[lp]["x"], dataset[lp]["y"])
plt.savefig(f"{r}trace-abs-ba.pdf")






'''
plt.clf()
#plt.ylim(0, 10)

samples=50000

freq = (max_ts-min_ts)/float(samples)
x = [min_ts+i*freq for i in range(samples)]

fy = None
for lp in dataset:
	y = numpy.interp(x, dataset[lp]["x"], dataset[lp]["y"])
	if fy is None: fy = y
	else: fy += y

	plt.plot(x, y)
plt.savefig(f"{r}trace2-abs.pdf")
plt.clf()
if "base" not in r: plt.ylim(0, 50)

plt.plot(x, fy)
plt.savefig(f"{r}sum-abs.pdf")
f.close()
'''
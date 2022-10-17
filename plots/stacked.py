import matplotlib.pyplot as plt

aggregate = [[] for j in range(5)]
with open("tbc_stats_auto.txt", "r") as f:
    for line in f.readlines():
        for i, v in enumerate(line.split()):
            aggregate[i].append(int(v))

tbc_cats = ["healthy", "infected", "sick", "treatment", "treated"]

fig, ax = plt.subplots()
ax.stackplot(range(len(aggregate[0])), aggregate, labels=tbc_cats, alpha=0.8)
ax.legend(loc='upper center')
ax.set_title('Population')
ax.set_xlabel('Day')
ax.set_ylabel('People')

plt.show()

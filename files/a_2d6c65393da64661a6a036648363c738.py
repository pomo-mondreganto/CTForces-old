import numpy as np

def prettyprint(a, b, c):
    with open('stump.out', 'w') as f:
        f.write(' '.join([str(a), str(b), str(c)]))

def bst(segm):
    return np.polyfit(np.zeros_like(segm), segm, 0)[0]
    return segm.mean()

def main():
    with open('stump.in', 'r') as f:
        n = int(f.readline())
        pts = np.array(sorted([list(map(np.int, i.split())) for i in f.readlines()]))

    def get_params(t):
        a = bst(pts[:t, 1])
        b = bst(pts[t:, 1])
        c = pts[t, 0]
        return a, b, c

    def pred(a, b, c):
        x = pts[:, 0]
        return b * (x >= c) + a * (x < c)

    def q(a, b, c):
        return np.sum((pred(a, b, c) - pts[:, 1]) ** 2)

    if n == 0:
        while 1:
            pass
    
    if n == 1:
        prettyprint(pts[0, 1], pts[0, 1], pts[0, 0])
        return

    if n == 2:
        prettyprint(pts[0, 1], pts[1, 1], pts[1, 0])
        return

    minerr = -1
    best_t = 1

    for t in range(1, n):
        a, b, c = get_params(t)
        err = q(a, b, c)
        # print(t, err)
        if minerr == -1 or err < minerr:
            minerr = err
            best_t = t
        assert(minerr >= 0)

    a, b, c = get_params(best_t)
    prettyprint(a, b, c)
    
main()
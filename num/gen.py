import random, os
r = random.randint
T = 200
tests = ''
for t in xrange(T):
    f = open('%d.in' % t, 'w')
    for _ in xrange(10):
        if t < T-2:
            f.write('%d\n' % (r(0,100)))
        elif t == T-2:
            f.write('%d\n' % (r(int(-1e12), int(-4e9))))
        else:
            f.write('%d\n' % (r(int(-1e20), int(-1e19))))
    f.close()
    os.system('python sol.py < %d.in > %d.out' % (t, t))
    tests += '%d %d.in %d.out\n' % (t, t, t)
f = open('tests', 'w')
f.write(tests)
f.close()

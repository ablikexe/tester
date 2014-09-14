import random, os
random.seed(0)
TASK = 'num'
path = lambda s: TASK + '/' + s
r = random.randint
T = 200
tests = ''
for t in xrange(T):
    f = open(path('%d.in') % t, 'w')
    for _ in xrange(10):
        if t < T-2:
            f.write('%d\n' % (r(0,100)))
        elif t == T-2:
            f.write('%d\n' % (r(int(-1e12), int(-4e9))))
        else:
            f.write('%d\n' % (r(int(-1e20), int(-1e19))))
    f.close()
    os.system('python %s < %s > %s' % (path('sol.py'), path('%d.in'%t), path('%d.out'%t)))
    tests += '%d %d.in %d.out\n' % (t, t, t)
f = open(path('tests'), 'w')
f.write(tests)
f.close()

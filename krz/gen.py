import random, os
random.seed(0)
TASK = 'krz'
path = lambda s: TASK + '/' + s
r = random.randint
T = 200
tests = ''
for t in xrange(T):
    f = open(path('%d.in' % t), 'w')
    f.write('%d %d %d\n' % (r(4,30000), r(4,30000), r(4,300000000)))
    f.close()
    os.system('python %s < %s > %s' % (path('sol.py'), path('%d.in' % t), path('%d.out' % t)))
    tests += '%d %d.in %d.out\n' % (t, t, t)
f = open(path('tests'), 'w')
f.write(tests)
f.close()

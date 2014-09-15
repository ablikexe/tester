import random, os
random.seed(0)
TASK = 'cho'
path = lambda s: TASK + '/' + s
r = random.randint
T = 10
tests = ''
for t in xrange(T):
    f = open(path('%d.in' % t), 'w')
    f.write('%d\n' % (10**6)**(0.1*(t+1)))
    f.close()
    os.system('python %s < %s > %s' % (path('sol.py'), path('%d.in' % t), path('%d.out' % t)))
    tests += '%d %d.in %d.out\n' % (t, t, t)
f = open(path('tests'), 'w')
f.write(tests)
f.close()

r = input()
res = 0
for x in xrange(1,r+1):
    y = int((r*r - x*x)**0.5)
    res += y
print 4*res

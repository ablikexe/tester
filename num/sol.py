a = [input() for _ in xrange(10)]
print max(range(10), key=a.__getitem__)+1

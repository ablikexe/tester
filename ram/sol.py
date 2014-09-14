n, m = map(int, raw_input().split())
print '#'*m + '\n' + ('#' + '.'*(m-2) + '#\n')*(n-2) + '#'*m + '\n'

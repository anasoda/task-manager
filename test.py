import os
# from pprint import pprint
for i in os.environ.keys():
    if len(i) < 10:
        print(20*"_")
        print(f'{i} => {os.environ[i]}')

# x = os.environ["PATH"].split(';')
# for p in x:
#     print(20*"_")
#     print(f'{p}')
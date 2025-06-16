import os
import sys
import csv

def organize(filelist):
    reader = csv.reader(filelist, delimiter=',')
    header = next(reader)
    for row in reader:
        index = 'out/%s.bin' % (row[0])
        filename = 'out/%s/%s' % (row[2], row[1])
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        if os.path.exists(index):
            os.rename(index, filename)
        else:
            print(f"Warning: {index} does not exist")

def main(argc, argv):
    if argc != 1:
        print(f'Usage: {argv[0]}')
        return 1
    with open('filelist.csv', 'r', newline='', encoding='utf-8') as filelist:
        organize(filelist)
    return 0

if __name__ == '__main__':
    sys.exit(main(len(sys.argv), sys.argv))

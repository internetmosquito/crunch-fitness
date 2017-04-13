import sys, getopt

from cr.db.store import Settings
from cr.db.loader import load_data

"""
A lightweight wrapper on load_data to create and populate db outside cr.db module
"""


def create_db(arguments):
    import ipdb; ipdb.set_trace()
    clean = False
    try:
        opts, args = getopt.getopt(arguments, 'hc', ['clean'])
    except getopt.GetoptError:
        print('createdb.py -c')
        sys.exit(2)

    for opt, arg in opts:
        if opt == '-h':
            print('createdb.py -c')
            sys.exit()
        elif opt in ('-c', '--clean'):
            clean = True

    settings = Settings()
    settings.url = 'mongodb://localhost:27017/crunchdb'
    import ipdb; ipdb.set_trace()
    load_data(settings, clean)


if __name__ == "__main__":
    clean = sys.argv[1:]
    create_db(clean)

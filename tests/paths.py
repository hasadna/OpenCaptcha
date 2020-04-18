import os


def data_file(path):
    this_dir = os.path.dirname(__file__)
    data_dir = os.path.join(this_dir, 'testdata')
    return os.path.join(data_dir, path)

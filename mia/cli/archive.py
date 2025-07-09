from mia.archiver.web import WebArchiver

def archive(args):
    with WebArchiver() as wa:
        wa.archive("https://ja.stackoverflow.com/")




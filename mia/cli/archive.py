from mia.archiver.web import WebArchiver

def archive(args):
    wa = WebArchiver()
    wa.archive("https://stackoverflow.com")
    wa.d.quit()




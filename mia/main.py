from .archiver import WebArchiver

wa = WebArchiver()
wa.archive("https://stackoverflow.com")
wa.d.quit()




from kivymd.uix.screen import MDScreen


class LoadingWindow(MDScreen):
    def __init__(self, **kwargs):
        super(LoadingWindow, self).__init__(**kwargs)
        self.name = "LoadingWindow"

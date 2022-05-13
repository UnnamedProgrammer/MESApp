from kivymd.uix.screen import MDScreen


class MainWindow(MDScreen):
    def __init__(self, **kwargs):
        super(MainWindow, self).__init__(**kwargs)
        self.name = "MainWindow"

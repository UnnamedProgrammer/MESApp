from kivymd.uix.screen import MDScreen


class MainScreen(MDScreen):
    def __init__(self, **kwargs):
        super(MainScreen, self).__init__(**kwargs)
        self.name = "MainScreen"

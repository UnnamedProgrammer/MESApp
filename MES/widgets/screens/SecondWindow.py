from kivymd.uix.screen import MDScreen

class SecondWindow(MDScreen):
    def __init__(self, **kwargs):
        super(SecondWindow, self).__init__(**kwargs)
        self.name = "SecondWindow"
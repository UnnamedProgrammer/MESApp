from kivymd.uix.screen import MDScreen

class IdleWindow(MDScreen):
    def __init__(self, **kwargs):
        super(IdleWindow, self).__init__(**kwargs)
        self.name = "idleWindow"
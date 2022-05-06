from kivy.uix.boxlayout import BoxLayout

class ContentNavigationDrawer(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'

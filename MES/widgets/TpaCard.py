from kivymd.uix.card import MDCard
from kivy.properties import StringProperty, ListProperty
from numpy import average


class TpaCard(MDCard):
    name = StringProperty()
    techstateEam = StringProperty()
    techstateTerminal = StringProperty()
    installedPf = StringProperty()
    LEamColor = ListProperty()
    LMesColor = ListProperty()
    productsPlan = StringProperty()
    products = StringProperty()
    cyclenorm = StringProperty()
    averagecycle = StringProperty()
    weightnorm = StringProperty()

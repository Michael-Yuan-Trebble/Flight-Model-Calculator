from PyQt5.QtWidgets import QStackedWidget
from screens.SelectScreen import SelectScreen
from screens.CreateAircraft import CreateAircraft
from screens.Home import Home
from screens.AirSpeedIndicationGraph import AirSpeedIndicationGraph
from screens.TurnPerformance import TurnPerformance
from screens.ThrustGraph import ThrustGraph

class NavigationController:
    
    """
    Handles navigation between different app screens
    
    Manages switching between layouts (eg., Select Screen -> Home) and keeps track of the current screen
    """
    
    def __init__(self):
        self.stack = QStackedWidget()
        self.screens = {}
        
        self.startScreen = SelectScreen(self)
        self.startScreen.fileSelected.connect(self.goToHome)
        self.startScreen.createAircraft.connect(self.goToCreateCharacter)
        
        self.addScreen("start",self.startScreen)
        
        self.setCurrent("start")
        
    def addScreen(self,name,widget):
        self.screens[name] = widget
        self.stack.addWidget(widget)    
    
    def setCurrent(self,name):
        if name in self.screens:
            self.stack.setCurrentWidget(self.screens[name])
        else:
            raise ValueError(f"Screen {name} not found")
    
    def show(self):
        self.stack.setWindowTitle("Aircraft Calculator")
        self.stack.setGeometry(250,250,600,500)
        self.stack.show()

    # ----- Changing Screens -----

    def goToStart(self):
        self.setCurrent("start")
    
    # ----- Emit Signals -----
    
    def goToHome(self, filePath=None):
        self.homeScreen = Home(self,filePath)
        self.homeScreen.createCharacterSignal.connect(self.goToCreateCharacter)
        self.homeScreen.createGraphSignal.connect(self.goToGraph)
        self.homeScreen.createAirSpeed.connect(self.goToAir)
        self.homeScreen.createThrust.connect(self.goToThrust)
        self.addScreen("home",self.homeScreen)
        self.setCurrent("home")
    
    def goToCreateCharacter(self,filePath=None):
        self.createCharacterScreen = CreateAircraft(filePath)
        self.createCharacterScreen.finished.connect(self.goToHome)
        self.addScreen("createChar",self.createCharacterScreen)
        self.setCurrent("createChar")
    
    def goToGraph(self,filePath=None):
        self.createGraph = AirSpeedIndicationGraph(filePath)
        self.createGraph.finished.connect(self.goBack)
        self.addScreen("createGraph",self.createGraph)
        self.setCurrent("createGraph")
        
    def goToAir(self,filePath=None):
        self.createAir = TurnPerformance(filePath)
        self.createAir.finished.connect(self.goBack)
        self.addScreen("createAir",self.createAir)
        self.setCurrent("createAir")
        
    def goToThrust(self,filePath=None):
        self.createThrust = ThrustGraph(filePath)
        self.createThrust.finished.connect(self.goBack)
        self.addScreen("createThrust",self.createThrust)
        self.setCurrent("createThrust")
        
    # ----- Go Back to Home -----
        
    def goBack(self):
        self.setCurrent("home")
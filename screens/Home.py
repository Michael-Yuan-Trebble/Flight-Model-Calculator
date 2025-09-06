from PyQt5.QtWidgets import QDialog, QWidget, QPushButton, QLabel, QHBoxLayout, QVBoxLayout, QFileDialog, QStackedWidget, QLineEdit
import json
from PyQt5.QtCore import Qt, pyqtSignal

class Home(QWidget):
    
    """
    Home Screen that displays all essentials
    
    The root page that all other pages will default to
    """
    
    createCharacterSignal = pyqtSignal(str)
    createGraphSignal = pyqtSignal(str)
    createAirSpeed = pyqtSignal(str)
    createThrust = pyqtSignal(str)
    def __init__(self,controller,file):
        super().__init__()
        self.controller = controller
        self.file = file
        self.initUI()
        
    def initUI(self):
        try:
            with open(self.file,"r") as f:
                self.data = json.load(f)
        except(FileNotFoundError,json.JSONDecodeError):
            raise RuntimeError("Home file not found error")
        
        self.main = QVBoxLayout()
        self.setLayout(self.main)
        self.readCharacterName()
        row2 = QHBoxLayout()
        self.button = QPushButton("Graph")
        self.button.clicked.connect(self.emitGraph)
        row3 = QHBoxLayout()
        self.button2 = QPushButton("Graph Air")
        self.button2.clicked.connect(self.emitAir)
        row4 = QHBoxLayout()
        self.button3 = QPushButton("Graph Thrust")
        self.button3.clicked.connect(self.emitThrust)
        row2.addWidget(self.button)
        row3.addWidget(self.button2)
        row4.addWidget(self.button3)
        self.main.addLayout(row2)
        self.main.addLayout(row3)
        self.main.addLayout(row4)
        
    # ----- Emissions -----
        
    def emitGraph(self):
        self.createGraphSignal.emit(self.file)
    def emitAir(self):
        self.createAirSpeed.emit(self.file)
    def emitThrust(self):
        self.createThrust.emit(self.file)
        
    # ----- Start Populating Screen 
        
    def readCharacterName(self):
        row1 = QHBoxLayout()
        name = "None"
        if "aircraft" in self.data and "name" in self.data["aircraft"]:
            name = self.data["aircraft"]["name"]
        
        self.label = QLabel(f"Aircraft: {name}")
        self.editNameButton = QPushButton("Edit")
        row1.addWidget(self.label)
        row1.addWidget(self.editNameButton)
        self.editNameButton.clicked.connect(self.editNameClick)
        
        row2 = QHBoxLayout()
        designation = "None"
        if "aircraft" in self.data and "Designation" in self.data["aircraft"]["stats"]:
            designation = self.data["aircraft"]["stats"]["Designation"]
        self.label2 = QLabel(f"Designation: {designation}")
        row2.addWidget(self.label2)
        
        self.main.addLayout(row1)
        self.main.addLayout(row2)

        
    # ----- Create popups and read results -----
    
    def editNameClick(self):
        popup = EditCharacterNamePopup(self.data,self.file,self)
        if popup.exec() == QDialog.Accepted:
            self.label.setText(f"Aircraft: {self.data["aircraft"]["name"]}")

"""
Edit button popup if the user wants to change their character's name

"""

class EditCharacterNamePopup(QDialog):
    def __init__(self,data,file,parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        self.data = data
        self.file = file
        self.setModal(True)
        
        layout = QVBoxLayout()
        
        self.label = QLabel("Aircraft:")
        self.nameInput = QLineEdit()
        self.nameInput.setPlaceholderText("Enter Aircraft Name...")
        self.label.setBuddy(self.nameInput)
        
        layout.addWidget(self.label)
        layout.addWidget(self.nameInput)
        row1 = QHBoxLayout()
        okButton = QPushButton("Cancel")
        okButton.clicked.connect(self.reject)
        setButton = QPushButton("Set")
        setButton.clicked.connect(lambda: self.changeCharacterName(self.nameInput.text().strip()))
        row1.addWidget(okButton)
        row1.addWidget(setButton)
        layout.addLayout(row1)
        self.setLayout(layout)
    
    def changeCharacterName(self,name=None):
        self.data["aircraft"]["name"] = name
        with open(self.file, "w") as f:
            json.dump(self.data,f,indent=4)
        self.accept()
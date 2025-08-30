from PyQt5.QtWidgets import QWidget, QPushButton, QLabel, QHBoxLayout, QVBoxLayout, QFileDialog, QMessageBox, QLineEdit, QDialog
from PyQt5.QtCore import pyqtSignal, Qt
import json, os

class SelectScreen(QWidget):
    
    """
    First screen for the aircraft data application
    
    Handles either the creation of a new .json file, or loading of an existing .json file
    """
    
    fileSelected = pyqtSignal(str)
    createAircraft = pyqtSignal(str)
    def __init__(self, controller):
        super().__init__()
        self.controller = controller
        self.initUI()
        
    def initUI(self):
        self.createProfile = QPushButton("Create")
        self.createProfile.setObjectName("createButton")
        self.createProfile.clicked.connect(self.selectFolder)
        
        self.uploadProfile = QPushButton("Upload")
        self.uploadProfile.clicked.connect(self.openFileDialog)
        
        self.master = QHBoxLayout()  
        col1 = QVBoxLayout()
        col2 = QVBoxLayout()
        col1.addWidget(self.createProfile)
        col2.addWidget(self.uploadProfile)
        
        self.master.addLayout(col1, 50)
        self.master.addLayout(col2, 50)
        
        self.setLayout(self.master)
    
    # ----- Open File Branch -----    
    
    def openFileDialog(self):
        filePath, _ = QFileDialog.getOpenFileName(
            self,
            "Open File",
            "",
            "Text Files (*.json)"
        )
        if filePath:
            self.fileSelected.emit(filePath)
        else:
            raise RuntimeError("ERROR!")
    
    def selectFolder(self):
        self.folder = QFileDialog.getExistingDirectory(self,"Select Folder")
        if self.folder:
            self.saveFile()
        else:
            QMessageBox.warning(self,"Canceled","No folder selected!")
            
    # ----- Create File Branch -----
            
    def saveFile(self): 
        self.clearLayout(self.master)
        row1 = QHBoxLayout()
        self.label = QLabel()
        self.label.setText("Enter File Name:")
        self.nameInput = QLineEdit()
        self.nameInput.setPlaceholderText("Enter file name...")
        self.nameInput.returnPressed.connect(self.saveButtonEnter)
        row1.addWidget(self.label)
        row1.addWidget(self.nameInput)
        self.master.addLayout(row1)
        self.setLayout(self.master)
        
    def saveButtonEnter(self):
        self.fileName = self.nameInput.text().strip()
        if not self.fileName.endswith(".json"):
            self.fileName += ".json"
        self.filePath = os.path.join(self.folder,self.fileName)
        self.initializeFile()
            
    def initializeFile(self):
        
        # ----- Filling .json with major sections for later -----
        
        try:
            with open(self.filePath,"r") as f:
                self.data = json.load(f)
        except(FileNotFoundError,json.JSONDecodeError):
            self.data = {}
            
        if "aircraft" not in self.data:
            self.data["aircraft"] = {}
        
        aircraftDetails = ["weight","thrust","drag"]
        
        self.data["aircraft"]["name"] = None
        self.data["aircraft"]["stats"] = {}
        
        #for detail in aircraftDetails:
        #    self.data["aircraft"]["stats"][detail] = 0.0
        
        with open(self.filePath, "w") as f:
            json.dump(self.data,f,indent=4)
        QMessageBox.information(self,"Success",f"File created at:\n{self.filePath}")
        self.askCreateStats()
        
    def askCreateStats(self):
        popup = CreateAircraftPopup(self)
        if popup.exec() == QDialog.Accepted:
            self.createAircraft.emit(self.filePath)
        else:
            self.fileSelected.emit(self.filePath)
        
    # ----- Clear Everything On Screen -----
        
    def clearLayout(self,layout):
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
            else:
                self.clearLayout(item.layout())
                
class CreateAircraftPopup(QDialog):
    def __init__(self,parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        self.setModal(True)
        layout = QVBoxLayout()
        label = QLabel("Would you like to create the Aircraft right now?")
        layout.addWidget(label)
        row1 = QHBoxLayout()
        okButton = QPushButton("Yes")
        okButton.clicked.connect(self.accept)
        setButton = QPushButton("No")
        setButton.clicked.connect(self.reject)
        row1.addWidget(okButton)
        row1.addWidget(setButton)
        layout.addLayout(row1)
        self.setLayout(layout)
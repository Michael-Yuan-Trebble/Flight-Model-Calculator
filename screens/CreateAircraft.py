from PyQt5.QtWidgets import QWidget,  QLabel, QHBoxLayout, QVBoxLayout,QMessageBox, QLineEdit, QPushButton, QDialog, QComboBox, QCheckBox
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QDoubleValidator
import json,os

class CreateAircraft(QWidget):
    
    """
    New Character Creation screen
    
    Handles choices of character info (eg., class and background) and stores in the loaded .json file
    """
    
    finished = pyqtSignal(str)
    
    def __init__(self, filePath = None):
        super().__init__()
        self.filePath = filePath
        
        self.loadFiles()
        self.initUI()
        
    # ----- Load all necessary custom .jsons -----
        
    def loadFiles(self):
        current_dir = os.path.dirname(os.path.abspath(__file__))
        parent_dir = os.path.dirname(current_dir)
        newFolder = os.path.join(parent_dir,"customs")
        os.makedirs(newFolder,exist_ok=True)
        
        self.fileName = "CustomDesignations.json"
        desPath = os.path.join(newFolder,self.fileName)
        try:
            with open(desPath,"r") as f:
                self.desData = json.load(f)
        except(FileNotFoundError,json.JSONDecodeError):
            self.desData = {}
            
        try:
            with open(self.filePath,"r") as f:
                self.data = json.load(f)
        except(FileNotFoundError,json.JSONDecodeError):
            raise RuntimeError("Error File Not Found (CreateAircraft self.data)!")
        
    def initUI(self):
        self.master = QVBoxLayout()
        
        row1 = QHBoxLayout()
        self.label = QLabel("Aircraft Name:")
        self.nameInput = QLineEdit()
        self.nameInput.setPlaceholderText("Enter Aircraft Name...")
        self.label.setBuddy(self.nameInput)
        self.confirmButton = QPushButton("Confirm")
        self.confirmButton.clicked.connect(self.setName)
        
        row1.addWidget(self.label)
        row1.addWidget(self.nameInput)
        row1.addWidget(self.confirmButton)
        
        self.nameInput.returnPressed.connect(self.setName)
        self.master.addLayout(row1)
        self.setLayout(self.master)
    
    # ----- Name input -----    
    
    def setName(self):
        self.aircraftName = self.nameInput.text().strip()
        if not self.aircraftName:
            return
        
        self.data["aircraft"]["name"] = self.aircraftName
        
        with open(self.filePath, "w") as f:
            json.dump(self.data,f,indent=4)

        self.setStats()
            
    # ----- Set Aircraft Stats -----
    
    def setStats(self):
        self.clearLayout(self.master)
        
        self.confirmButton = QPushButton("Confirm")
        self.confirmButton.clicked.connect(self.saveStats)
        
        self.desData
        designations = ["Fighter", "Multirole","Attack/Strike","Bomber","AWACS","Electronic-Warfare","Passenger","Cargo","Utility","Pedestrian"]
        for key in self.desData["designations"]:
            designations.append(key)
        
        designations.sort()
        
        self.combo = QComboBox()
        self.combo.addItem("Custom...")
        self.combo.addItems(designations)
        self.aircraftLabels = ["Weight","Thrust","After Burner Power","Drag","Wing Area","Wing Span","Thrust To Weight","CL Slope","CL Max","Alpha Stall"]
        
        self.labels = {name: QLabel() for name in self.aircraftLabels}
        
        for label in self.aircraftLabels:
            self.labels[label].setText(f"{label}:")
        
        self.inputTexts = {name: QLineEdit() for name in self.aircraftLabels}
        
        for input in self.aircraftLabels:
            self.inputTexts[input].setValidator(QDoubleValidator())
            self.inputTexts[input].setPlaceholderText(f"Enter {input}...")
            self.labels[label].setBuddy(self.inputTexts[input])
        
        for key in self.aircraftLabels:
            rowLayout = QHBoxLayout()
            rowLayout.addWidget(self.labels[key])
            rowLayout.addWidget(self.inputTexts[key])
            self.master.addLayout(rowLayout)
        
        self.row = QHBoxLayout()
        
        self.checkBox = QCheckBox("Hard cap at CL Max")
        self.checkBox.setChecked(False)
        self.row.addWidget(self.checkBox)
        
        self.lineEdit = QLineEdit()
        self.lineEdit.setPlaceholderText("Drop after stall (%)...")
        self.lineEdit.setEnabled(True)
        self.row.addWidget(self.lineEdit)
        
        self.checkBox.toggled.connect(self.toggleLineEdit)
        
        self.master.addLayout(self.row)
        self.master.addWidget(self.combo)
        self.master.addWidget(self.confirmButton)
            
    def toggleLineEdit(self,checked):
        self.lineEdit.setEnabled(not checked)
            
    def saveStats(self):
        for text in self.aircraftLabels:
            inputText = self.inputTexts[text].text().strip()
            if not inputText:
                self.data["aircraft"][text] = 0.0
            else:
                self.data["aircraft"]["stats"][text] = float(inputText)
        aircraftClass = self.combo.currentText()
        self.data["aircraft"]["stats"]["Post-Stall Behaviour"] = {}
        if self.checkBox.isChecked():
            self.data["aircraft"]["stats"]["Post-Stall Behaviour"]["Is Capped"] = True
        else:
            self.data["aircraft"]["stats"]["Post-Stall Behaviour"]["Is Capped"] = False
            self.data["aircraft"]["stats"]["Post-Stall Behaviour"]["Percentage"] = self.lineEdit.text()
        if aircraftClass == "Custom...":
            popup = CreateClassPopup(self.data,self.filePath,self)
            if popup.exec() == QDialog.Rejected:
                return
        else:
            self.data["aircraft"]["stats"]["Designation"] = aircraftClass
        with open(self.filePath, "w") as f:
            json.dump(self.data,f,indent=4)
        QMessageBox.information(self,"Saved","Info saved")

        self.end()
    
    # ----- Clear widgets on screen -----
    
    def clearLayout(self,layout):
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
            else:
                self.clearLayout(item.layout())
    
    # ----- Go back to Home ------
    
    def end(self):
        self.finished.emit(self.filePath)

"""

Create Custom Class and add it to a file for future storage

"""

class CreateClassPopup(QDialog):
    def __init__(self,data,filePath,parent=None):
        super().__init__(parent)
        self.data = data
        self.filePath = filePath
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        self.setModal(True)
        self.main = QVBoxLayout()
        self.input = QLineEdit()
        self.input.setPlaceholderText("Custom Class...")
        label = QLabel("Custom Class Name:")
        label.setBuddy(self.input)
        self.main.addWidget(label)
        self.main.addWidget(self.input)
        row1 = QHBoxLayout()
        okButton = QPushButton("Confirm")
        okButton.clicked.connect(self.saveClass)
        setButton = QPushButton("Back")
        setButton.clicked.connect(self.reject)
        row1.addWidget(okButton)
        row1.addWidget(setButton)
        self.main.addLayout(row1)
        self.setLayout(self.main)
        
    def saveClass(self):
        current_dir = os.path.dirname(os.path.abspath(__file__))
        parent_dir = os.path.dirname(current_dir)
        newFolder = os.path.join(parent_dir,"customs")
        os.makedirs(newFolder,exist_ok=True)
        
        self.fileName = "CustomDesignations.json"
        desPath = os.path.join(newFolder,self.fileName)
        
        with open(desPath,"r") as f:
            self.desData = json.load(f)
        
        if "designations" not in self.desData:
            self.desData["designations"] = {}
            
        if self.input.text().strip() in self.desData["designations"]:
            rejections = QLabel("Already Exists")
            self.main.addWidget(rejections)
            return

        self.desData["designations"][self.input.text().strip()] = {}
        self.data["aircraft"]["stats"]["designation"] = self.input.text().strip()
        
        with open(self.filePath, "w") as f:
            json.dump(self.data,f,indent=4)
        with open(desPath,"w") as f:
            json.dump(self.desData,f,indent=4)
        QMessageBox.information(self,"Saved","Class Saved")
        self.accept()
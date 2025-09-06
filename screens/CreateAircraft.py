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

        designations = ["Fighter", "Multirole", "Attack/Strike", "Bomber", "AWACS",
                        "Electronic-Warfare", "Passenger", "Cargo", "Utility", "Pedestrian"]
        designations += list(self.desData.get("designations", []))
        designations.sort()
        self.combo = QComboBox()
        self.combo.addItem("Custom...")
        self.combo.addItems(designations)
        self.master.addWidget(self.combo)

        self.aircraftValueLabels = ["Weight","Thrust","Afterburner Power", "Wing Area", "Wing Span"]
        self.inputValueTexts = {}
        self.unitCombos = {}

        unitOptions = {
            "Weight": ["kg","t","lb"],
            "Thrust": ["lbf","kN","kgf"],
            "Afterburner Power": ["lbf","kN","kgf"],
            "Wing Area": ["ft²","m²"],
            "Wing Span": ["ft","m"]
        }

        for label in self.aircraftValueLabels:
            comboItems = unitOptions.get(label)
            row, lineEdit, combo = self.createLabeledInputs(label, comboItems)
            self.inputValueTexts[label] = lineEdit
            if combo:
                self.unitCombos[label] = combo
            self.master.addLayout(row)

        self.aircraftLabels = ["Thrust To Weight","CL Slope","CL Max","Alpha Stall"]
        self.inputTexts = {}
        for label in self.aircraftLabels:
            row, lineEdit, _ = self.createLabeledInputs(label)
            self.inputTexts[label] = lineEdit
            self.master.addLayout(row)

        self.row = QHBoxLayout()
        self.checkBox = QCheckBox("Hard cap at CL Max")
        self.checkBox.setChecked(False)
        self.checkBox.toggled.connect(self.toggleLineEdit)
        self.row.addWidget(self.checkBox)

        self.lineEdit = QLineEdit()
        self.lineEdit.setPlaceholderText("Drop after stall (%)...")
        self.row.addWidget(self.lineEdit)
        self.master.addLayout(self.row)

        self.master.addWidget(self.confirmButton)
        
    def createLabeledInputs(self, labelText, comboItems=None,placeholder=True):
        row = QHBoxLayout()
        label = QLabel(f"{labelText}")
        lineEdit = QLineEdit()
        lineEdit.setValidator(QDoubleValidator())
        if placeholder:
            lineEdit.setPlaceholderText(f"Enter {labelText}...")
        label.setBuddy(lineEdit)
        row.addWidget(label)
        row.addWidget(lineEdit)
        
        combo = None
        if comboItems:
            combo = QComboBox()
            combo.addItems(comboItems)
            row.addWidget(combo)
    
        return row, lineEdit, combo
            
    def toggleLineEdit(self,checked):
        self.lineEdit.setEnabled(not checked)
            
    def saveStats(self):
        stats = {}

        for key, lineEdit in self.inputValueTexts.items():
            text = lineEdit.text().strip()
            value = float(text) if text else 0.0
            unit = self.unitCombos[key].currentText() if key in self.unitCombos else None
            stats[key] = {"value": value, "unit": unit}

        for key, lineEdit in self.inputTexts.items():
            text = lineEdit.text().strip()
            stats[key] = float(text) if text else 0.0

        postStall = {"Is Capped": self.checkBox.isChecked()}
        if not self.checkBox.isChecked():
            postStall["Percentage"] = self.lineEdit.text()
        stats["Post-Stall Behaviour"] = postStall

        aircraftClass = self.combo.currentText()
        if aircraftClass == "Custom...":
            popup = CreateClassPopup(self.data, self.filePath, self)
            if popup.exec() == QDialog.Rejected:
                return
        else:
            stats["Designation"] = aircraftClass

        self.data["aircraft"]["stats"] = stats
        with open(self.filePath, "w") as f:
            json.dump(self.data, f, indent=4)

        QMessageBox.information(self, "Saved", "Info saved")
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
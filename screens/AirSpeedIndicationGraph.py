from PyQt5.QtWidgets import QWidget, QPushButton, QLabel, QHBoxLayout, QVBoxLayout, QLineEdit
import json
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtGui import QDoubleValidator
import numpy as np
import pyqtgraph as pg
    
"""
Create a graph of the difference betweeen TAS and IAS speeds between altitudes

This calculation is not plane dependent and is the same for every
"""

class AirSpeedIndicationGraph(QWidget):
    
    finished = pyqtSignal()
    def __init__(self,file):
        super().__init__()
        self.file = file
        self.initUI()
        
    def initUI(self):
        try:
            with open(self.file,"r") as f:
                self.data = json.load(f)
        except(FileNotFoundError,json.JSONDecodeError):
            raise RuntimeError("Home file not found error")
        
        self.main = QVBoxLayout()
        self.row1 = QHBoxLayout()
        self.row2 = QHBoxLayout()
        self.row3 = QHBoxLayout()
        self.row4 = QHBoxLayout()
        self.title = QLabel("TAS vs IAS")
        self.row1.addWidget(self.title)
        pg.setConfigOption('background','w')
        pg.setConfigOption('foreground','k')
        self.plotWidget = pg.PlotWidget()
        self.row2.addWidget(self.plotWidget)
        
        self.plot()
        self.inputTAS = QLineEdit()
        self.inputTAS.setPlaceholderText("Enter TAS Speed...")
        self.inputTAS.setValidator(QDoubleValidator())
        self.plotAgain = QPushButton("Plot")
        self.plotAgain.clicked.connect(self.plot)
        
        self.row3.addWidget(self.inputTAS)
        self.row3.addWidget(self.plotAgain)
        
        self.backButton = QPushButton("Go Back")
        self.backButton.clicked.connect(self.goBack)
        self.row4.addWidget(self.backButton)
        
        self.main.addLayout(self.row1)
        self.main.addLayout(self.row2)
        self.main.addLayout(self.row3)
        self.main.addLayout(self.row4)
        
        self.setLayout(self.main)
    
    def goBack(self):
        self.finished.emit()
        
    # ----- Calculating TAS and CAS differences -----
        
    def returnTPRho(self,hm):
        
        T0 = 288.15 #In Kelvin
        L = 0.0064 #K/m lapse rate up to 11km
        p0 = 101325 #In Pa
        g0 = 9.80665 # gravity in m/s^2
        R = 287.05287 #in J
        
        T = T0 - L*hm
        p = p0 * (T/T0)**(g0/(R*L))
        rho = p/(R*T)
        return T,p,rho

    def returnTASfromCASAlt(self,VIASkt,hft):
        R = 287.05287 #in J
        T0 = 288.15 #In Kelvin
        p0 = 101325 #In Pa
        gamma = 1.4
        Vc = VIASkt * 0.514444
        h = hft
        a0 = (gamma*R*T0)**0.5
        qc0 = p0 * ((1+(gamma-1)/2 * (Vc/a0)**2)**(gamma/(gamma-1))-1)
        T,p,_ = self.returnTPRho(h)
        M = ((2/(gamma-1)) * ((1+qc0/p)**((gamma-1)/gamma)-1))**0.5
        a = (gamma*R*T)**0.5
        VTAS = a*M
        return VTAS/0.514444

    def returnTASminusIAS(self,VIASkt=120,hminft=0,hmaxft=40000,stepft=500):
        alts = np.arange(hminft,hmaxft+stepft,stepft,dtype=float)
        tas = np.array([self.returnTASfromCASAlt(VIASkt,h)for h in alts])
        delta = tas-VIASkt
        return alts,delta,tas

    # ----- Plot the difference

    def plot(self,VIASKt=120,hminft=0,hmaxft=40000,stepft=500):
        try:
            V = float(self.inputTAS.text())
            alts,delta,tas = self.returnTASminusIAS(V,hminft,hmaxft,stepft)
        except:
            alts,delta,tas = self.returnTASminusIAS(VIASKt,hminft,hmaxft,stepft)
        self.plotWidget.clear()
        self.plotWidget.setLabel('left','TAS - IAS (kt)',color='k',size='14pt')
        self.plotWidget.setLabel('bottom','Altitude (ft)',color='k',size='14pt')
        self.plotWidget.showGrid(x=True,y=True,alpha=0.3)
        self.plotWidget.plot(alts,delta,pen=pg.mkPen(width=2))
        
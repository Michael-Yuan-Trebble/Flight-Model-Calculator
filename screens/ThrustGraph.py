from PyQt5.QtWidgets import QWidget, QPushButton, QLabel, QHBoxLayout, QVBoxLayout, QLineEdit
import json
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtGui import QDoubleValidator
import math
import numpy as np
import pyqtgraph as pg

class ThrustGraph(QWidget):
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
        self.title = QLabel("Thrust")
        self.row1.addWidget(self.title)
        pg.setConfigOption('background','w')
        pg.setConfigOption('foreground','k')
        self.plotWidget = pg.PlotWidget()
        self.row2.addWidget(self.plotWidget)
        
        self.convertSI()
        self.inputTAS = QLineEdit()
        self.inputTAS.setPlaceholderText("Enter TAS Speed...")
        self.inputTAS.setValidator(QDoubleValidator())
        self.plotAgain = QPushButton("Plot")
        #self.plotAgain.clicked.connect(self.plot)
        
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
    
    
    def convertSI(self):
        pref = self.data["aircraft"]["stats"]
        self.wingArea = pref["Wing Area"]["value"]
        
        if pref["Wing Area"]["unit"] == "ft\u00b2":
            self.wingArea = self.wingArea * 0.092903
        
        self.wingSpan = pref["Wing Span"]["value"]
        
        if pref["Wing Span"]["unit"] == "ft":
            self.wingSpan = self.wingSpan * 0.3048
        
        self.weight = pref["Weight"]["value"]
        conversions = {
            "kg":9.80665,
            "t":1000 * 9.80665,
            "lb":4.448,
        }
        factor = conversions.get(pref["Weight"]["unit"],1)
        self.weight =self.weight * factor
        
        self.thrust = pref["Thrust"]["value"]
        conversions = {
            "lbf": 4.44822,
            "kgf": 9.80665,
            "kN": 1000,
        }
        factor = conversions.get(pref["Thrust"]["unit"],1)
        self.thrust = self.thrust * factor
        self.e = 0.8
        self.inducedDrag()
        
    def inducedDrag(self):
        AR = self.wingSpan**2/self.wingArea
        VArray = np.linspace(10,400,300)
        k = 1.0 / (math.pi * AR * self.e)
        rho, altM = self.rhoFromUserAlt()
        
        CD0 = 0.012
        
        q = 0.5 * rho * VArray**2
        CL = self.weight / (q * self.wingArea)
        CD = CD0 + k * CL**2
        TReq = q * self.wingArea * CD
        TReq = TReq
        rho0 = 1.225
        sigma = rho / rho0
        TAvail = self.thrust * (0.7 + 0.3 * sigma)
        TAvail = TAvail 
        TAvailCurve = np.full_like(VArray,TAvail)
        
        diff = TReq - TAvailCurve
        CrossingsIndex = np.where(np.sign(diff[:-1]) != np.sign(diff[1:]))[0]
        maxLevelSpeed = None
        if CrossingsIndex.size > 0:
            i = CrossingsIndex[-1]
            x0,x1 = VArray[i],VArray[i+1]
            y0,y1 = diff[i], diff[i+1]
            frac = -y0/ (y1 - y0)
            maxLevelSpeed = x0 + frac * (x1 - x0)
        plotItem = self.plotWidget.plotItem
        plotItem.clear()
        plotItem.setLabel("bottom","Speed",units="m/s")
        plotItem.setLabel("left","Thrust",units="N")
        try:
            legend = plotItem.legend
        except AttributeError:
            legend = plotItem.addLegend()
        plotItem.plot(VArray,TReq,pen=pg.mkPen('r',width=2), name="Thrust Required (D)")
        plotItem.plot(VArray,TAvailCurve,pen=pg.mkPen('b',width=2,style=pg.QtCore.Qt.DashLine),name="Thrust Available")
        if maxLevelSpeed is not None:
            TAtV = np.interp(maxLevelSpeed,VArray,TReq)
            scatter = pg.ScatterPlotItem([maxLevelSpeed],[TAtV],symbol='o',size=8,brush='k')
            plotItem.addItem(scatter)
            text = pg.TextItem(html=f"<div style='color:black'>VMax = {maxLevelSpeed:.1f} m/s </div>", anchor=(0,1))
            text.setPos(maxLevelSpeed,TAtV)
            plotItem.addItem(text)
        
    def rhoFromUserAlt(self):
        altText = None
        if altText is None:
            altM = 1000
        else:
            txt = altText.text().strip()
            altM = float(txt) if txt else 1000
        _, rho, _ = self.atmosphere(altM)
        return rho, altM
        
    def atmosphere(self,altM):
        g = 9.80665
        gamma = 1.4
        R = 287.05
        T0 = 288.15
        p0 = 101325
        L = -0.0065
        if altM <= 11000:
            T = T0 + L * altM
            p = p0 * (T/T0) ** (-g / (L*R))
        else:
            T = 216.65
            p = p0 * 0.22336 * np.exp(-g*(altM - 11000) / (R*T))
        rho = p/(R*T)
        a = np.sqrt(gamma*R*T)
        return T,rho,a
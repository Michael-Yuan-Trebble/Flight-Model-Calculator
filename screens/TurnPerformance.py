from PyQt5.QtWidgets import QWidget, QPushButton, QLabel, QHBoxLayout, QVBoxLayout, QLineEdit
import json
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtGui import QDoubleValidator
import numpy as np
import pyqtgraph as pg

"""
Create a graph showing the turning performance at different speeds (represented by Mach speed) at different altitudes

Red represents the Instantaneous turn rate, which is limited by CLMax and the g-limit (currently at 9Gs)

Green represents Sustained turn rate (turning without losing energy) and is determined by thrust and drag
"""    

class TurnPerformance(QWidget):
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
        self.row5 = QHBoxLayout()
        self.title = QLabel("Turn Performance")
        self.row1.addWidget(self.title)
        pg.setConfigOption('background','w')
        pg.setConfigOption('foreground','k')
        self.plotWidget = pg.PlotWidget()
        self.plotLift = pg.PlotWidget(title="Lift Curve")
        self.plotTurn = pg.PlotWidget(title="Turn Performance")
        self.row2.addWidget(self.plotLift)
        self.row2.addWidget(self.plotTurn)
        
        self.row3.addWidget(self.plotWidget)
        
        self.plot()
        self.inputTAS = QLineEdit()
        self.inputTAS.setPlaceholderText("Enter TAS Speed...")
        self.inputTAS.setValidator(QDoubleValidator())
        self.plotAgain = QPushButton("Plot")
        self.plotAgain.clicked.connect(self.plot)
        
        self.row4.addWidget(self.inputTAS)
        self.row4.addWidget(self.plotAgain)
        
        self.backButton = QPushButton("Go Back")
        self.backButton.clicked.connect(self.goBack)
        self.row5.addWidget(self.backButton)
        
        self.main.addLayout(self.row1)
        self.main.addLayout(self.row2)
        self.main.addLayout(self.row3)
        self.main.addLayout(self.row4)
        self.main.addLayout(self.row5)
        self.plot()
        
        self.setLayout(self.main)
       
    """
    Curve showing lift for the aircraft at speeds
    
    Uses capped or drop off percentage to represent different aero on different planes
    """
        
    def liftCurve(self,alphaDeg):
        pref = self.data["aircraft"]["stats"]
        postStall = pref["Post-Stall Behaviour"]
        
        alphaRad = np.radians(alphaDeg)
        
        CL = pref["CL Slope"] * alphaRad
        
        alphaStall = pref["Alpha Stall"]
        CLMax = pref["CL Max"]
        CLSlope = pref["CL Slope"]
        
        if alphaDeg <= alphaStall:
            CL = CLSlope * alphaRad
            return min(CL,CLMax)
        else:
            if postStall["Is Capped"]:
                return CLMax
            else:
                pct = float(postStall["Percentage"])
                CLMin = CLMax * pct
                dropWidth = 5.0
                alphaDropEnd = alphaStall + dropWidth
                if alphaDeg <= alphaDropEnd:
                    t = (alphaDeg - alphaStall) / dropWidth
                    return CLMax * (1-t) + CLMin * t
                else:
                    return CLMin
    
    """
    Calculating physics felt by aircraft, uses speeds at kt (will change to be adaptable to user input)
    """
    
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
    
    def machToTAS(self,mach,altM):
        _,rho,a = self.atmosphere(altM)
        V = mach*a
        return V, rho
    
    def instantaneousMax(self,CLMax,S,W,rho,V,gLimit = 9):
        q = 0.5 * rho * V**2
        n = q * CLMax * S / W
        return min(n,gLimit)
    
    def turnRateFromN(self,n,V):
        g = 9.80665
        if n <= 1.0:
            return 0
        omega = g * np.sqrt(n**2 - 1.0) / V
        return omega * 180.0 /np.pi
    
    def specificExcessPower(self,TForce,DForce,V,W):
        return (TForce - DForce) * V / W
    
    def sustainedN(self,V,rho,S,W,TAvail,CD0,k,gLimit=9):
        q = 0.5 * rho * V**2
        nCandidates = np.linspace(1.0,gLimit,200)
        best = 1
        for n in nCandidates:
            CL = n * W / (q * S)
            CD = CD0 + k * CL**2
            D = q * S * CD
            if TAvail >= D:
                best = n
            else:
                break
        return best

    # ----- Plotting all lines -----
                
    def plot(self):
        
        pref = self.data["aircraft"]["stats"]
        CLMax = pref["CL Max"]
        wingArea = pref["Wing Area"]
        wingSpan = pref["Wing Span"]
        weight = pref["Weight"]
        thrust = pref["Thrust"]
        drag = pref["Drag"]
        altM = 3000
        machVals = np.linspace(0.2,1.5,100)
        
        turnRatesInstant = []
        turnRatesSustainedPS = []
        
        for m in machVals:
            V, rho = self.machToTAS(m,altM)
            k = 1.0 / (np.pi * ((wingSpan**2)/wingArea)*0.8)
            CL = weight / (0.5 * rho * V ** 2 * wingArea)
            CD = 0.02 + k * CL**2
            dragC = 0.5 * rho * V**2 * wingArea * CD
            
            nInst = self.instantaneousMax(CLMax,wingArea,weight,rho,V,9.0)
            trInst = self.turnRateFromN(nInst,V)
            turnRatesInstant.append(trInst)
            
            nSust = self.sustainedN(V,rho,wingArea,weight,(thrust * (rho/1.225)),CD,k,9)
            trSust = self.turnRateFromN(nSust,V)
            turnRatesSustainedPS.append(trSust)
        
        self.plotLift.plotItem.clear()
        self.plotTurn.plotItem.clear()
        
        alphas = np.linspace(-5,30,200)
        
        CLs = [self.liftCurve(a) for a in alphas]
        
        self.plotWidget.plotItem.clear()
        self.plotWidget.plotItem.plot(alphas,CLs,pen=pg.mkPen('r',width=2))
        
        self.plotTurn.plotItem.plot(machVals,turnRatesInstant,pen=pg.mkPen('r',width=2),name="Instantaneous")
        self.plotTurn.plotItem.plot(machVals,turnRatesSustainedPS,pen=pg.mkPen('g',width=2),name="Sustained")
        

    # ----- Go back to Home -----

    def goBack(self):
        self.finished.emit()
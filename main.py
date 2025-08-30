import sys
from PyQt5.QtWidgets import QApplication
from Navigation import NavigationController

# Applying QSS Stylesheet to program
def load_stylesheet(app,filename):
    with open(filename,"r") as f:
        app.setStyleSheet(f.read())

if __name__ in "__main__":
    
    app = QApplication([])
    
    load_stylesheet(app,"main.qss")
    
    # Create Navigation Controller, starting the program
    controller = NavigationController()
    controller.show()
    
    sys.exit(app.exec_())
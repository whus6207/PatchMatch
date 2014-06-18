
#FileName   : testgui.py
#project    : VFX final project


import numpy as np
from PyQt4 import QtCore, QtGui 
import cv2

#img = cv2.imread('..\image\example.jpg',1)
#img.shape
#cv2.line(img,(0,0),(200,200),(255,255,255),5)
#cv2.namedWindow('image',cv2.WINDOW_NORMAL)
#cv2.imshow('image',img)
#cv2.waitKey(0)
#cv2.destroyAllWindows()

class line(QtGui.QWidget):
    def __init__(self, point1, point2):
        self.p1 = point1
        self.p2 = point2
        
    def paintEvent(self,event):
        painter=QPainter()
        painter.begin(self)
        painter.setPen(QPen(Qt.darkGray,3))
        painter.drawLine(self.p1,self.p2)
        painter.end()

class MyCentralLabel(QtGui.QLabel):
    def __init__(self):
        super(MyCentralLabel,self).__init__()
        self.my_image =QtGui.QImage()
        self.cv_img = None
        
    def mousePressEvent(self,event):
        print(">>mousePress")
        self.startx=event.x()
        self.starty=event.y()
    def mouseReleaseEvent(self,event):
        print(">>mouseRelease")
        self.endx=event.x()
        self.endy=event.y()
        newLine = line(QtCore.QPoint(self.startx, self.starty), QtCore.QPoint(self.endx, self.endy))
    def loadImage(self):
        file_name= QtGui.QFileDialog.getOpenFileName(self,self.tr("Open a file"),'.')
        self.cv_img=cv2.imread(str(file_name))
        #cv2.imshow("Show Image with OpencV", self.cv_img)

        height, width, bytesPerComponent = self.cv_img.shape
        bytesPerLine = bytesPerComponent * width;
        cv2.cvtColor(self.cv_img, cv2.cv.CV_BGR2RGB, self.cv_img)
        self.my_image = QtGui.QImage(self.cv_img.data, width, height, bytesPerLine, QtGui.QImage.Format_RGB888)
        self.setPixmap(QtGui.QPixmap.fromImage(self.my_image))
        self.resize(self.my_image.width(),self.my_image.height())
        #self.statusBar().showMessage(file_name)
    def saveImage(self):
        pass
    def drawLine(self):
        my_painter=QtGui.QPainter()
        my_painter.begin(self.my_image)
        my_painter.drawLine(20,20,100,100)
        my_painter.end()
    def drawRec(self):
        pass
    def drawMask(self):
        pass

class MyCentralWidget(QtGui.QWidget):

    def __init__(self):
        super(MyCentralWidget,self).__init__()
    #    self.initUI()
        
    #def initUI(self):
    #    grid = QtGui.QGridLayout()
    #    self.my_pixmap = QtGui.QPixmap(self)
    #    grid.addWidget(self.my_pixmap)

    
class MyMainWindow(QtGui.QMainWindow):
    def __init__(self):
        super (MyMainWindow,self).__init__()
        
        self.ctl_label =MyCentralLabel()
        self.regAct()
        self.initUI()

    def regAct(self):
        self.exitAction = QtGui.QAction('&Exit',self)
        self.exitAction.setShortcut('Ctrl+Q')
        self.exitAction.setStatusTip('Exit application')
        self.exitAction.triggered.connect(QtGui.qApp.quit)
        self.loadAction = QtGui.QAction('&Load',self)
        self.loadAction.setShortcut('Ctrl+L')
        self.loadAction.setStatusTip('Loading image...')
        self.loadAction.triggered.connect(self.ctl_label.loadImage)
        self.saveAction = QtGui.QAction('&Save',self)
        self.saveAction.setShortcut('Ctrl+S')
        self.saveAction.setStatusTip('Saving image...')
        self.saveAction.triggered.connect(self.ctl_label.saveImage)
        self.lineAction = QtGui.QAction('&Line',self)
        self.lineAction.setStatusTip('pick start and end point')
        self.lineAction.triggered.connect(self.ctl_label.drawLine)
    def initUI(self):
        #filemenu implementation
        menubar = self.menuBar()
        myFileMenu = menubar.addMenu('&File')
        myFileMenu.addAction(self.exitAction)
        myFileMenu.addAction(self.loadAction)
        myFileMenu.addAction(self.saveAction)

        myDrawMenu = menubar.addMenu('&Draw')
        myDrawMenu.addAction(self.lineAction)
        #myDrawMenu.addAction(self, '&rec')
        #myDrawMenu.addACtion(self, '&Mask')
        #central widget
        
        self.setCentralWidget(self.ctl_label)
        
        self.statusBar().showMessage("Ready")
        self.resize(600,500)
        self.setWindowTitle("VFX Final Project")
        self.show()
   
    
        
def main():
    myapp = QtGui.QApplication(sys.argv)
    ex = MyMainWindow()
    
    sys.exit( myapp.exec_() )
    
    

if __name__== "__main__":
    import sys
    main()



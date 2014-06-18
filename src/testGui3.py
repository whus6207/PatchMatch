#import sip
#sip.setapi('QString', 2)
#sip.setapi('QVariant', 2)

from PyQt4 import QtCore, QtGui
import cv2
import numpy as np
lineBuf=[]
rectBuf=[]


def np2img(cv_image):
    height, width, bytesperComponent =cv_image.shape
    bytesperLine = bytesperComponent* width
    cv2.cvtColor(cv_image, cv2.cv.CV_BGR2RGB, cv_image)
    my_image = QtGui.QImage(cv_image.data, width, height, bytesperLine, QtGui.QImage.Format_ARGB32)
    return my_image
def img2np(my_image):
    my_image = my_image.convertToFormat( QtGui.QImage.Format_RGB32)
    width = my_image.width()
    height = my_image.height()
    ptr = my_image.bits()
    ptr.setsize(my_image.byteCount())
    arr = np.array(ptr).reshape(height, width,4)#[:, :, :3]
    return arr
    
class MarkPara:
    def __init__ (self,p1,p2):
        self.point1 =p1
        self.point2 =p2
    def p1(self):
        return point1
    def p2(self):
        return point2
    
class DrawArea(QtGui.QWidget):

    def __init__(self, parent=None):
        super(DrawArea, self).__init__(parent)

        self.setAttribute(QtCore.Qt.WA_StaticContents)
        self.modified = False
        self.scribbling = False
        self.lineFlg =False
        self.recFlg = False
        self.maskFlg = False
        self.myPenWidth = 1
        self.myPenColor = QtCore.Qt.blue
        imageSize = QtCore.QSize(500, 500)
        self.cv_image =None
        self.src_image = QtGui.QImage(imageSize, QtGui.QImage.Format_ARGB32)
        self.op_image = QtGui.QImage(imageSize, QtGui.QImage.Format_ARGB32)
        self.op_image.fill( QtCore.Qt.transparent)
        self.lastPoint = QtCore.QPoint()

    def initOpImage(self):
        new_size = self.src_image.size()
        self.op_image =QtGui.QImage(new_size, QtGui.QImage.Format_ARGB32)
        self.op_image.fill( QtCore.Qt.transparent)
        
    def openImage(self, fileName):
        loadedImage = QtGui.QImage()
        if not loadedImage.load(fileName):
            return False
        self.cv_image =img2np(loadedImage)
        cv2.imshow("Show Image with OpencV", self.cv_image)
        w = loadedImage.width()
        h = loadedImage.height()    
        self.mainWindow.resize(w, h)
        
        #self.src_image = loadedImage
        self.src_image =np2img(self.cv_image)
        self.initOpImage()
        
        self.modified = False
        self.update()
        return True

    def saveImage(self, fileName, fileFormat):
        visibleImage = self.src_image
        self.resizeImage(visibleImage, self.size())

        if visibleImage.save(fileName, fileFormat):
            self.modified = False
            return True
        else:
            return False

    def setPenColor(self, newColor):
        self.myPenColor = newColor

    def setPenWidth(self, newWidth):
        self.myPenWidth = newWidth

    def clearImage(self):
        self.src_image.fill(QtGui.qRgb(255, 255, 255))
        self.op_image.fill(QtGui.qRgb(255, 255, 255))
        self.modified = True
        self.update()

    def drawLine(self):
        self.lineFlg = True#not self.lineFlg
    def drawRec(self):
        self.recFlg = True#not self.recFlg
    def drawMask(self):
        self.maskFlg = True#not self.maskFlg

    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton and self.maskFlg:
            self.lastPoint = event.pos()
            self.scribbling = True
        if event.button() == QtCore.Qt.LeftButton and self.lineFlg:
            self.lastPoint = event.pos()
            self.scribbling = True
        if event.button() == QtCore.Qt.LeftButton and self.recFlg:
            self.lastPoint = event.pos()
            self.scribbling = True

    def mouseMoveEvent(self, event):
        if (event.buttons() & QtCore.Qt.LeftButton) and self.scribbling and self.maskFlg:
            self.drawLineTo(event.pos())
        
            

    def mouseReleaseEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton and self.scribbling and self.maskFlg:
            self.drawLineTo(event.pos())
            self.scribbling = False
            self.maskFlg = False
        if event.button() == QtCore.Qt.LeftButton and self.scribbling and self.lineFlg:
            lineBuf.append( MarkPara(self.lastPoint, event.pos() ) )
            #print(len(lineBuf))
            self.drawLineTo(event.pos())
            self.scribbling = False
            self.lineFlg = False
        if event.button() == QtCore.Qt.LeftButton and self.scribbling and self.recFlg:
            rectBuf.append( MarkPara(self.lastPoint, event.pos() ) )
            self.drawRect(event.pos())
            self.scribbling = False
            self.recFlg = False

    def paintEvent(self, event):
        
        painter = QtGui.QPainter(self)
        painter.setCompositionMode(QtGui.QPainter.CompositionMode_SourceOver)
        painter.drawImage(event.rect(), self.src_image)
        painter.drawImage(event.rect(), self.op_image,)

    def resizeEvent(self, event):
        self.resizeImage(self.src_image, event.size())
        self.resizeImage(self.op_image, event.size())
        super(DrawArea, self).resizeEvent(event)

    def drawLineTo(self, endPoint):
        painter = QtGui.QPainter(self.op_image)
        painter.setPen(QtGui.QPen(self.myPenColor, self.myPenWidth,
            QtCore.Qt.SolidLine, QtCore.Qt.RoundCap, QtCore.Qt.RoundJoin))
        painter.drawLine(self.lastPoint, endPoint)
        self.modified = True
        
        self.update()
        self.lastPoint = QtCore.QPoint(endPoint)

    def drawRect(self, endPoint):
        painter = QtGui.QPainter(self.op_image)
        painter.setPen(QtGui.QPen(self.myPenColor, self.myPenWidth,
            QtCore.Qt.SolidLine, QtCore.Qt.RoundCap, QtCore.Qt.RoundJoin))
        print( type(self.lastPoint))
        print( type(endPoint))
        painter.drawRects( QtCore.QRect( self.lastPoint, endPoint ) )
        self.modified = True
        
        self.update()
        self.lastPoint = QtCore.QPoint(endPoint)

    def resizeImage(self, image, newSize):
        if image.size() == newSize:
            return

        newImage = QtGui.QImage(newSize, QtGui.QImage.Format_RGB32)
        newImage.fill(QtGui.qRgb(255, 255, 255))
        painter = QtGui.QPainter(newImage)
        painter.drawImage(QtCore.QPoint(0, 0), image)




        self.src_image = newImage

    def print_(self):
        printer = QtGui.QPrinter(QtGui.QPrinter.HighResolution)

        printDialog = QtGui.QPrintDialog(printer, self)
        if printDialog.exec_() == QtGui.QDialog.Accepted:
            painter = QtGui.QPainter(printer)
            rect = painter.viewport()
            size = self.src_image.size()
            size.scale(rect.size(), QtCore.Qt.KeepAspectRatio)
            painter.setViewport(rect.x(), rect.y(), size.width(), size.height())
            painter.setWindow(self.src_image.rect())
            painter.drawImage(0, 0, self.src_image)
            painter.end()

    def isModified(self):
        return self.modified

    def penColor(self):
        return self.myPenColor

    def penWidth(self):
        return self.myPenWidth

    ##
    def myInpaint(self):
        pass
    def myRetarget(self):
        pass
    def srcUpdate(self,new_src):
        self.src_image = new_src
        self.update()

class MainWindow(QtGui.QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()

        self.saveAsActs = []

        self.scribbleArea = DrawArea(self)
        self.scribbleArea.clearImage()
        self.scribbleArea.mainWindow = self  
        self.setCentralWidget(self.scribbleArea)

        self.createActions()
        self.createMenus()

        self.setWindowTitle("VFX Final")
        self.resize(500, 500)

    def closeEvent(self, event):
        if self.maybeSave():
            event.accept()
        else:
            event.ignore()

    def open(self):
        if self.maybeSave():
            fileName = QtGui.QFileDialog.getOpenFileName(self, "Open File",
                QtCore.QDir.currentPath())
            if fileName:
                self.scribbleArea.openImage(fileName)

    def save(self):
        action = self.sender()
        fileFormat = action.data()
        self.saveFile(fileFormat)

    def penColor(self):
        newColor = QtGui.QColorDialog.getColor(self.scribbleArea.penColor())
        if newColor.isValid():
            self.scribbleArea.setPenColor(newColor)

    def penWidth(self):
        newWidth, ok = QtGui.QInputDialog.getInteger(self, "Scribble",
            "Select pen width:", self.scribbleArea.penWidth(), 1, 50, 1)
        if ok:
            self.scribbleArea.setPenWidth(newWidth)

    def createActions(self):
        self.openAct = QtGui.QAction("&Open...", self, shortcut="Ctrl+O",
            triggered=self.open)

        for format in QtGui.QImageWriter.supportedImageFormats():
            format = str(format)

            text = format.upper() + "..."

            action = QtGui.QAction(text, self, triggered=self.save)
            action.setData(format)
            self.saveAsActs.append(action)

        self.printAct = QtGui.QAction("&Print...", self,
            triggered=self.scribbleArea.print_)

        self.exitAct = QtGui.QAction("E&xit", self, shortcut="Ctrl+Q",
            triggered=self.close)

        self.penColorAct = QtGui.QAction("&Pen Color...", self,
            triggered=self.penColor)

        self.penWidthAct = QtGui.QAction("Pen &Width...", self,
            triggered=self.penWidth)

        self.clearScreenAct = QtGui.QAction("&Clear Screen", self,
            shortcut="Ctrl+L", triggered=self.scribbleArea.clearImage)

        self.lineAct = QtGui.QAction("draw line",self)
        self.lineAct.triggered.connect(self.scribbleArea.drawLine)
        self.recAct =   QtGui.QAction("draw Rec",self)
        self.recAct.triggered.connect(self.scribbleArea.drawRec)
        self.maskAct =  QtGui.QAction("draw Mask",self)
        self.maskAct.triggered.connect(self.scribbleArea.drawMask)

        self.inpaintAct = QtGui.QAction("inpaint",self)
        self.inpaintAct.triggered.connect(self.scribbleArea.myInpaint)
        self.retargetAct = QtGui.QAction("retarget",self)
        self.retargetAct.triggered.connect(self.scribbleArea.myRetarget)


    def createMenus(self):
        self.saveAsMenu = QtGui.QMenu("&Save As", self)
        for action in self.saveAsActs:
            self.saveAsMenu.addAction(action)

        fileMenu = QtGui.QMenu("&File", self)
        fileMenu.addAction(self.openAct)
        fileMenu.addMenu(self.saveAsMenu)
        fileMenu.addAction(self.printAct)
        fileMenu.addSeparator()
        fileMenu.addAction(self.exitAct)

        optionMenu = QtGui.QMenu("&Options", self)
        optionMenu.addAction(self.penColorAct)
        optionMenu.addAction(self.penWidthAct)
        optionMenu.addSeparator()
        optionMenu.addAction(self.clearScreenAct)

        markMenu = QtGui.QMenu("&Mark",self)
        markMenu.addAction(self.lineAct)
        markMenu.addAction(self.recAct)
        markMenu.addAction(self.maskAct)

        runMenu = QtGui.QMenu("&Run",self)
        runMenu.addAction(self.inpaintAct)
        runMenu.addAction(self.retargetAct)

        self.menuBar().addMenu(fileMenu)
        self.menuBar().addMenu(optionMenu)
        self.menuBar().addMenu(markMenu)
        self.menuBar().addMenu(runMenu)


    def maybeSave(self):
        if self.scribbleArea.isModified():
            ret = QtGui.QMessageBox.warning(self, "Scribble",
                "The image has been modified.\n"
                "Do you want to save your changes?",
                QtGui.QMessageBox.Save | QtGui.QMessageBox.Discard |
                QtGui.QMessageBox.Cancel)
            if ret == QtGui.QMessageBox.Save:
                return self.saveFile('png')
            elif ret == QtGui.QMessageBox.Cancel:
                return False

        return True

    def saveFile(self, fileFormat):
        initialPath = QtCore.QDir.currentPath() + '/untitled.' + fileFormat

        fileName = QtGui.QFileDialog.getSaveFileName(self, "Save As",
            initialPath,
            "%s Files (*.%s);;All Files (*)" % (fileFormat.upper(), fileFormat))
        if fileName:
            return self.scribbleArea.saveImage(fileName, fileFormat)

        return False


if __name__ == '__main__':

    import sys

    app = QtGui.QApplication(sys.argv)
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec_())

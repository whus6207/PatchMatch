import abc

class absGUI:
  """ Abstract GUI class """
  __metaclass__ = abc.ABCMeta

  # show image
  @abc.abstractmethod
  def setImg(self, img):
    """ set the current displaying image to img"""
    return

  @abc.abstractmethod
  def getImg(self):
    """ get the current displaying image without mask and lines"""
    return 

  @abc.abstractmethod
  def getMask(self):
    """ get the current mask image(none zero indicate the masked area) as list """
    return []

  @abc.abstractmethod
  def getLines(self):
    """ get the current line as list """
    # [(startpoint1, endpoint1), (startpoint2, endpoint2)]
    return []

  @abc.abstractmethod
  def clear(self):
    """ clear the mask and the lines, return bool value for success or not """
    return 
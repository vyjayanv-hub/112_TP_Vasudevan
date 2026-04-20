from cmu_graphics import *

def onAppStart(app):
    app.height = 890
    app.width = 680
    app.margin = 30
    app.lineHeight = 18
    app.fontSize = 14
    app.books = dict()
    app.fileName = 'pg844.txt'
    rawText = loadBook(app.fileName)
    
    charsPerLine = (app.width - 2 * app.margin) // (app.fontSize * 0.6)
    linesPerPage = (app.height - 120) // app.lineHeight
    app.charsPerPage = int(charsPerLine * linesPerPage)
    app.pages = makePages(rawText, app.charsPerPage)
    app.pageIndex = 0
    app.totalPages = len(app.pages)
    makeButtons(app)
    app.readingScreen = False
    app.defaultScreen = True
    app.usingCamera = True
    app.cursorX = 200
    app.cursorY = 200
    app.offset = 10
    app.curvedEdgeRadius = 10
    app.curvedEdgeOffset = 19
    app.burgerPressed = False
    app.displayScreenOffsetY = 6
    app.displayScreenOffsetX = 8
    app.displayScreenTop = 90
    app.displayScreenLeft = 88
    app.displayScreenWidth = 490
    app.displayScreenHeight = 650


    app.menuWidth = 100
    app.burgerAndMenuOffset = 22
    app.menuHeight = 180

def makeBooks(app):
    app.earnestWilde = Books(100, 100, 'The Picture of Dorian Gray', 'Oscar Wilde', 254, 'pg844.cover.medium.jpg')
    app.littleWomenAlcott = Books(100, 200, 'Little Women', 'Louisa May Alcott', 499, 'pg25344.cover.medium.jpg')
    app.gatsbyFitzgerald = Books(100, 300, 'The Great Gatsby', 'Scott Fitzgerald', 180, 'pg64317.cover.medium.jpg')
    app.scarletHawthorne = Books(250, 100, 'The Scarlet Letter', 'Nathaniel Hawthorne', 272,'pg25344.cover.medium.jpg')

def makeButtons(app):
    app.buttons = []
    darkPastelBlue = rgb(115, 115, 115)

    app.libraryButton = Buttons(app.displayScreenLeft + app.displayScreenWidth - app.displayScreenOffsetX,
                                app.displayScreenTop + app.displayScreenOffsetY + app.burgerAndMenuOffset, 
                                app.menuWidth - 2.5, app.menuHeight//4,
                                'white', darkPastelBlue, 'Library', None )
    app.buttons.append(app.libraryButton)

def onKeyPress(app, key):
    if key == 'right' and app.pageIndex < app.totalPages - 1:
        app.pageIndex += 1
    elif key == 'left' and app.pageIndex > 0:
        app.pageIndex -= 1


def onMousePress(app, mouseX, mouseY):
    if app.readingScreen:
        if app.usingCamera:
            readingCamera(app)
            ####################make readingCamera
        readingMousePress(app, mouseX, mouseY)
    if app.defaultScreen:
        checkBurgerPressed(app, mouseX, mouseY)
        app.libraryButton = getButtonPressed(app, mouseX, mouseY)

def getButtonPressed(app, mouseX, mouseY):
    intersected = []
    for button in app.buttons:
        if button.intersect(mouseX, mouseY):
            intersected.append(button)
    return intersected


def checkBurgerPressed(app, mouseX, mouseY):
    hamburgerLineLength = 17
    spacing = 6
    upperY = app.displayScreenTop + app.displayScreenOffsetY
    lowerY = app.displayScreenTop + app.displayScreenOffsetY + spacing*2
    upperX = app.displayScreenLeft + app.displayScreenWidth - app.displayScreenOffsetX
    lowerX = app.displayScreenLeft + app.displayScreenWidth - app.displayScreenOffsetX - hamburgerLineLength
    if (lowerX <= mouseX <= upperX) and (upperY <= mouseY <= lowerY):
        app.burgerPressed = not app.burgerPressed

def readingMousePress(app, mouseX, mouseY):
    if mouseX > app.width /2:
        if app.pageIndex < app.totalPages - 1:
            app.pageIndex += 1
    else:
        if app.pageIndex > 0:
            app.pageIndex -= 1

def redrawAll(app):
    if app.defaultScreen:
        drawDefaultScreen(app)
        drawHamburgerButton(app)
    if app.readingScreen:
        drawBook(app)
    #cursor
    drawCircle(app.cursorX, app.cursorY, 10, fill='darkBlue')
    if app.burgerPressed:
        drawBurgerMenu(app)
        
def drawBook(app):
    drawRect(0,0, app.width, app.height, fill = 'ivory')
    pageText = app.pages[app.pageIndex]
    drawWrappedText(app, pageText)
    drawLabel(f'Page {app.pageIndex + 1} of {app.totalPages}', app.width / 2, app.height - 20, fill='white', size = 13)

def drawWrappedText(app, text):
    maxWidth = app.width - 2*app.margin
    charsPerLine = int(maxWidth / (app.fontSize * 0.55))
    y = 70
    for paragraph in text.split('\n\n'):
        words = paragraph.split()
        line = ''
        for word in words:
            test = line + (' ' if line else '') + word
            if len(test) > charsPerLine:
                drawLabel(line, app.margin, y, align='left', size = app.fontSize, fill = 'black')
                y += app.lineHeight
                line = word
                if y > app.height - 50:
                    return
            else:
                line = test
        if line:
            drawLabel(line, app.margin, y, align = 'left', size = app.fontSize, fill='black')
            y += app.lineHeight
        y += app.lineHeight //2
        if y > app.height - 50:
            return

def onMouseMove(app, mouseX, mouseY):
    app.cursorX = mouseX
    app.cursorY = mouseY
    
    #BOUND MOUSE MOTIONif app.cursorY
    
def loadBook(filename):
    with open(f'Book_Text_Files/{filename}', 'r', encoding = 'utf-8') as f:
        text = f.read()
    marker = '*** START OF'
    startIdx = text.find(marker)
    if startIdx != -1:
        text = text[text.find('\n', startIdx)+1:]
    endMarker = '*** END OF'
    endIdx = text.find(endMarker)
    if endIdx != -1:
        text = text[:endIdx]
    return text.strip()

def makePages(text, charsPerPage = 800):
    paragraphs = text.split('\n\n')
    pages = []
    current = ''
    for para in paragraphs:
        para = para.strip()
        if not para:
            continue
        if len(current) + len(para) + 2 > charsPerPage:
            if current:
                pages.append(current.strip())
            current = para
        else:
            current = current + '\n\n' + para if current else para
    if current:
        pages.append(current.strip())
    return pages


def drawDefaultScreen(app):
    #make turqoise background
    turqoise = rgb(186, 221, 212)
    
    drawRect(0 + app.offset, 10 , app.width - 20, app.height - 20, fill = turqoise)
    drawCircle(app.width - app.curvedEdgeOffset, app.curvedEdgeOffset, app.curvedEdgeRadius, fill = turqoise)
    drawCircle(app.curvedEdgeOffset, app.curvedEdgeOffset, app.curvedEdgeRadius, fill = turqoise)
    drawCircle(app.curvedEdgeOffset, app.height - app.curvedEdgeOffset, app.curvedEdgeRadius, fill = turqoise)
    drawCircle(app.width - app.curvedEdgeOffset, app.height - app.curvedEdgeOffset, app.curvedEdgeRadius, fill = turqoise)
    #make gray
    
    defaultScreenURL = 'defaultScreen.png'
    imageWidth, imageHeight = getImageSize(defaultScreenURL)
    drawImage(defaultScreenURL, app.width//2, app.height//2 + 15, align='center', width=imageWidth*1.5, height=imageHeight*1.5)

    lightGray = rgb(226, 226, 226)
    darkGray = rgb(133, 133, 133)
    
def drawBurgerMenu(app):


    drawRect(app.displayScreenLeft + app.displayScreenWidth - app.displayScreenOffsetX - app.menuWidth,
             app.displayScreenTop + app.displayScreenOffsetY + app.burgerAndMenuOffset, app.menuWidth, app.menuHeight, fill='black')
    
    app.libraryButton.drawButton()
    

    
def drawHamburgerButton(app):
    hamburgerLineLength = 17
    hamburgerColor = rgb(115, 115, 115)
    spacing = 6
    drawLine(app.displayScreenLeft + app.displayScreenWidth - app.displayScreenOffsetX - hamburgerLineLength, app.displayScreenTop + app.displayScreenOffsetY, app.displayScreenLeft + app.displayScreenWidth - app.displayScreenOffsetX, app.displayScreenTop + app.displayScreenOffsetY, fill = hamburgerColor, lineWidth = 3)
    drawLine(app.displayScreenLeft + app.displayScreenWidth - app.displayScreenOffsetX - hamburgerLineLength, app.displayScreenTop + app.displayScreenOffsetY + spacing, app.displayScreenLeft + app.displayScreenWidth - app.displayScreenOffsetX, app.displayScreenTop + app.displayScreenOffsetY + spacing, fill = hamburgerColor, lineWidth = 3)
    drawLine(app.displayScreenLeft + app.displayScreenWidth - app.displayScreenOffsetX - hamburgerLineLength, app.displayScreenTop + app.displayScreenOffsetY + spacing*2, app.displayScreenLeft + app.displayScreenWidth - app.displayScreenOffsetX, app.displayScreenTop + app.displayScreenOffsetY + spacing*2, fill = hamburgerColor, lineWidth = 3)
class Buttons:
    def __init__(self, left, top, width, height, textColor, backgroundColor, text,imageURL):
        self.textColor = textColor
        self.backgroundColor = backgroundColor
        self.text = text
        self.width = width
        self.height = height
        self.left = left
        self.top = top
        if imageURL != None:
            self.URL = imageURL
    
    def __repr__(self):
        return f'button:{self.text}'
    
    def intersect(self, x, y):
        upperX = self.width + self.left
        upperY = self.height + self.top
        return self.left <= x <= upperX and self.top <= y <= upperY

    def drawButton(self):
        if None not in (self.left, self.top, self.width, self.height):
            drawRect(self.left, self.top, self.width, self.height, fill = self.backgroundColor)
            drawLabel(self.text, self.left - self.width//2, self.top + self.height//2, fill=self.textColor)
        else:
            raise Exception("Haven't set button size and position yet before drawing")
    
    def __hash__(self):
        return hash(str(self))
    
    def __eq__(self, other):
        return isinstance(other, Buttons) and (self.text, self.backgroundColor, self.textColor) == (other.text, other.backgroundColor, other.textColor)

class Books:
    def __init__(self, left, top, title, author, numPages, imageURL):
        self.left = left
        self.top = top
        self.title = title
        self.author = author
        self.coverImage = imageURL
        self.numPages = numPages
        self.currentlyReading = False
        self.currPage = 0
        self.currentlyOpen = False
    
    def drawCovers(self):
        for book in app.library:
            if book.coverImage != None:
                imageWidth, imageHeight = getImageSize(self.coverImage)
                drawImage(app.url, app.left, app.top, align='center',
              width=imageWidth//2, height=imageHeight//2)
    
    def __repr__(self):
        return f'book: Author{self.author} Title{self.title}'
    
    def __hash__(self):
        return hash(str(self))
    
    def __eq__(self, other):
        return isinstance(other, Books) and ((self.title, self.author) == (other.title, other.author))



def main():
    runApp()

main()
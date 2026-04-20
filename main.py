from cmu_graphics import *

def onAppStart(app):
    app.height = 600
    app.width = 410
    app.margin = 30
    app.lineHeight = 18
    app.fontSize = 14
    app.fileName = 'pg844.txt'
    rawText = loadBook(app.fileName)
    
    charsPerLine = (app.width - 2 * app.margin) // (app.fontSize * 0.6)
    linesPerPage = (app.height - 120) // app.lineHeight
    app.charsPerPage = int(charsPerLine * linesPerPage)
    app.pages = makePages(rawText, app.charsPerPage)
    app.pageIndex = 0
    app.totalPages = len(app.pages)
    
    app.reading = True
    app.defaultScreen = False
    app.showCursor = True
    app.cursorX = 200
    app.cursorY = 200
    app.offset = 10
    app.curvedEdgeRadius = 10
    app.curvedEdgeOffset = 19
    app.burgerPressed = False


def onKeyPress(app, key):
    if key == 'right' and app.pageIndex < app.totalPages - 1:
        app.pageIndex += 1
    elif key == 'left' and app.pageIndex > 0:
        app.pageIndex -= 1
##################
def onMousePress(app, mouseX, mouseY):
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
    if app.reading:
        drawBook(app)
    if app.showCursor:
        #insert image later
        drawCircle(app.cursorX, app.cursorY, 10, fill='darkBlue')
        
def drawBook(app):
    drawRect(0,0, app.width, app.height, fill = 'ivory')
    
    drawRect(0, 0, app.width, 50, fill='darkSlateGray')
    drawLabel('My Gutenberg Reader', app.width / 2, 25, fill = 'white', size = 18, bold=True)
    pageText = app.pages[app.pageIndex]
    drawWrappedText(app, pageText)
    
    drawRect(0, app.height - 40, app.width, 40, fill='darkSlateGray')
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
    
    
    ################################




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

def drawAllButtons(app):
    pastelDarkBlue = rgb(128,153,182)
    #cursorButton = Button('',pastelDarkBlue , None, 'cmu://1166168/46485232/cursor--v1.jpg',40, 20, cx, cy, clicked)
    #other button
    cursorButton.drawButton()
    #draw all buttons
    
def drawDefaultScreen(app):
    #make turqoise background
    turqoise = rgb(186, 221, 212)
    
    drawRect(0 + app.offset, 10 , app.width - 20, app.height - 20, fill = turqoise)
    drawCircle(app.width - app.curvedEdgeOffset, app.curvedEdgeOffset, app.curvedEdgeRadius, fill = turqoise)
    drawCircle(app.curvedEdgeOffset, app.curvedEdgeOffset, app.curvedEdgeRadius, fill = turqoise)
    drawCircle(app.curvedEdgeOffset, app.height - app.curvedEdgeOffset, app.curvedEdgeRadius, fill = turqoise)
    drawCircle(app.width - app.curvedEdgeOffset, app.height - app.curvedEdgeOffset, app.curvedEdgeRadius, fill = turqoise)
    #make gray
    
    defaultScreenURL = 'cmu://1166168/46510460/Screenshot+2026-04-17+at+2.55.49 PM.png'
    imageWidth, imageHeight = getImageSize(defaultScreenURL)
    drawImage(defaultScreenURL, app.width//2, app.height//2 + 15, align='center', width=imageWidth//2, height=imageHeight//1.7)

    lightGray = rgb(226, 226, 226)
    darkGray = rgb(133, 133, 133)
    
def drawBurgerMenu(app):
    menuWidth = 50
    drawRect(app.width - 30 - menuWidth, 55, menuWidth, 60, fill='black')
    
def drawHamburgerButton(app):
    hamburgerLineLength = 17
    hamburgerColor = rgb(115, 115, 115)
    spacing = 6
    startY = 65
    startX = app.width - 45
    drawLine(startX - hamburgerLineLength, startY, startX, startY, fill = hamburgerColor, lineWidth = 3)
    drawLine(startX - hamburgerLineLength, startY + spacing, startX, startY + spacing, fill = hamburgerColor, lineWidth = 3)
    drawLine(startX - hamburgerLineLength, startY + spacing*2, startX, startY + spacing*2,fill = hamburgerColor, lineWidth = 3)

class Buttons:
    def __init__(self, textColor, backgroundColor, text,imageURL, width, height, cx, cy, clicked):
        self.textColor = textColor
        self.backgroundColor = backgroundColor
        self.text = text
        self.width = width
        self.height = height
        self.cx = cx
        self.cy = cy
        self.URL = imageURL
        self.clicked = clicked
    
    def __repr__(self):
        return f'button:{self.text}'
    
    def drawButton(self):
        drawCircle(self.cx + self.width//2, self.cy - self.height//2, 10, fill = self.backgroundColor)
        drawCircle(self.cx - self.width//2, self.cy - self.height//2, 10, fill = self.backgroundColor)
        drawCircle(self.cx - self.width//2, self.cy + self.height//2, 10, fill = self.backgroundColor)
        drawCircle(self.cx + self.width//2, self.cy + self.height//2, 10, fill = self.backgroundColor)
        drawRect(self.cx - self.width//2, self.cy - self.height//2, self.width, self.height, fill = self.backgroundColor)
        drawLabel(self.text, cx, cy, fill = self.textColor)
    
    def __hash__(self):
        return hash(str(self))
    
    def __eq__(self, other):
        return isinstance(other, Buttons) and (self.text, self.backgroundColor, self.textColor) == (other.text, other.backgroundColor, other.textColor)

class Books:
    def __init__(self, left, top, title, author, numPages, currentlyReading, currPage, currentlyOpen):
        self.currentlyReading = currentlyReading
        self.left = left
        self.top = top
        self.title = title
        self.author = author
        self.numPages = numPages
        self.currentlyReading = currentlyReading
        self.currPage = currPage
        self.currentlyOpen = currentlyOpen
    
    def __repr__(self):
        return f'book: Author{self.author} Title{self.title}'
    
    def __hash__(self):
        return hash(str(self))
    
    def __eq__(self, other):
        return isinstance(other, book) and ((self.title, self.author) == (other.title, other.author))



def main():
    runApp()

main()
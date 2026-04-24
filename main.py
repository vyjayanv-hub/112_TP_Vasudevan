from cmu_graphics import *
import cv2
import mediapipe as mp
import threading
import time
from collections import deque

# Put this near the top of main.py
global_latest_hand_result = None

def _gestureCallback(result, output_image, timestamp_ms):
    global global_latest_hand_result
    global_latest_hand_result = result

def onAppStart(app):
    app.height = 890
    app.width = 680
    app.readingScreen = False
    app.defaultScreen = True
    app.libraryScreen = False
    app.books = []
    app.currentRead = None
    app.stepsPerSecond = 30



    app.bookSpaceY = 150
    app.numshelves = 3
    app.numBooksPerShelf = 5
    app.bookSpaceX = 125

    app.gestureModel = GestureModel()
    app.gestureController = GestureController(app.gestureModel)
    app.usingCamera = False

    app.fontSize = 14


    app.allHighlights = {}
    app.allNotes = {}
    app.notes = {}
    app.highlights = {}
    app.highlightStart = None
    app.showNotePopup = False
    app.notePopupText = ''
    app.activeHighlight = False #checks if highlight mode is on
    app.activeNote = False
    app.noteText = ''
    app.activeBookmark = False
    app.showNotesPanel = False
    app.notesScroll = 0

    app.showChapterPanel = False
    app.chapterScroll = 0
    app.chapters = []

    app.cursorX = 200
    app.cursorY = 200
    app.offset = 10
    app.curvedEdgeRadius = 10
    app.curvedEdgeOffset = 19
    app.burgerPressed = False
    app.displayScreenOffsetYTurqoise = app.height * 0.825
    app.displayScreenOffsetY = 15
    app.displayScreenOffsetX = 15
    app.displayScreenTop = 90
    app.displayScreenLeft = 88
    app.displayScreenWidth = 490
    app.displayScreenHeight = 650


    app.menuWidth = 100
    app.burgerAndMenuOffset = 22
    app.menuHeight = 180

    app.bookBoxLeft = 60
    app.bookBoxTop = 22
    app.bookBoxWidth = app.width - 60
    app.bookBoxHeight = app.height - 80
    app.margin = 30

    makeButtons(app)
    makeBooks(app)
    app.gestureModel = GestureModel()
    app.gestureController = GestureController(app.gestureModel)
    loadAllProgress(app)



# Standalone functions (outside any class) - you already have these, keep them
def saveAllProgress(app):
    with open('progress.txt', 'w') as progressFile:
        for book in app.books:
            bookmarkString = ','.join(str(p) for p in book.bookmarks)
            progressFile.write(f'BOOK|{book.title}|{book.currPage}|{bookmarkString}\n')
    with open('highlights.txt', 'w') as highlightsFile:
        for bookTitle, pageDict in app.allHighlights.items():
            for pageKey, rangeList in pageDict.items():
                for startChar, endChar in rangeList:
                    highlightFile.write(f'{bookTitle}|{pageKey}|{startChar}|{endChar}\n')
    with open('notes.txt', 'w') as notesFile:
        for bookTitle, pageDict in app.allNotes.items():
            for pageKey, noteText in pageDict.items():
                notesFile.write(f'{bookTitle}|{pageKey}|{noteText}\n')

def loadAllProgress(app):
    for book in app.books:
        book.loadProgress()
    try:
        with open('highlights.txt', 'r') as highlightFile:
            for line in highlightFile:
                parts = line.strip().split('|')
                if len(parts) == 4:
                    bookTitle = parts[0]
                    pageKey = parts[1]
                    startChar = parts[2]
                    endChar = parts[3]
                    if bookTitle not in app.allHighlights:
                        app.allHighlights[bookTitle] = dict()
                    if pageKey not in app.allHighlights[bookTitle]:
                        app.allHighlights[bookTitle][pageKey] = []
                    app.allHighlights[bookTitle][pageKey].append((startChar, endChar))
    except FileNotFoundError:
        pass
    try:
        with open('notes.txt', 'r') as notesFile:
            for line in notesFile:
                parts = line.strip().split('|')
                if len(parts) == 3:
                    bookTitle = parts[0]
                    pageKey = int(parts[1])
                    noteText = parts[2]
                    if bookTitle not in app.allNotes:
                        app.allHighlights[bookTitle][pageKey] = dict()
                    app.allNotes[bookTitle][pageKey] = noteText
    except FileNotFoundError:
        pass
        

###################################################
#AI for using gesture model
def onStep(app):
    global global_latest_hand_result
    
    # Check if the MediaPipe thread handed us a new result
    if global_latest_hand_result is not None:
        with app.gestureModel.lock:
            app.gestureModel.latestLandmark = (
                global_latest_hand_result.hand_landmarks[0]
                if global_latest_hand_result.hand_landmarks
                else None
            )
        
        # Reset the global variable so we don't process the same frame twice
        global_latest_hand_result = None


    if app.usingCamera and app.gestureModel is not None:
        app.gestureModel.processLatestLandmark()
        app.cursorX = app.gestureModel.fingerScreenX
        app.cursorY = app.gestureModel.fingerScreenY
        
        # 2. Only check for swipes if we are actively reading a book
        if app.readingScreen and app.gestureModel.swipeDetected:
            swipeDir = app.gestureModel.swipeDirection
            app.gestureModel.swipeDetected = False # Reset immediately
            
            # Page flipping logic
            if swipeDir == "LEFT" and app.pageIndex < app.totalPages - 1:
                app.pageIndex += 1
                savePageChangeOnKeyPress(app)
            elif swipeDir == "RIGHT" and app.pageIndex > 0:
                app.pageIndex -= 1
                savePageChangeOnKeyPress(app)
        
        # 3. If a swipe happened on a non-reading screen, reset it so it 
        # doesn't 'carry over' when the user eventually opens a book.
        elif app.gestureModel.swipeDetected:
            app.gestureModel.swipeDetected = False
    # If not using camera, onMouseMove handles app.cursorX/Y automatically
    
def readingScreen(app):
    #make pages or smth
    drawRect(app.width//3, 0, app.width//3, app.height, fill = 'salmon')
    

#some ai for loadbook and makepages for loading pages
def makeCurrentBook(app, book):
    
    if app.readingScreen:
        app.bookBoxLeft = app.displayScreenLeft
        app.bookBoxTop = app.displayScreenTop + 25
        app.bookBoxWidth = app.displayScreenWidth
        app.bookBoxHeight = app.height - 160
        app.currentRead = book
        title = book.title
        if title not in app.allHighlights:
            app.allHighlights[title] = dict()
        if title not in app.allNotes:
            app.allNotes[title] = dict()
        app.highlights = app.allHighlights[title]
        app.notes = app.allNotes[title]



        app.lineHeight = int(app.fontSize * 1.35)
        app.fileName =  book.getURL()
        rawText = loadBook(app.fileName)
        print(f'loaded: {app.fileName}, length: {len(rawText)}')  # add this

        charsPerLine = int((app.width - 2 * app.margin) // (app.fontSize * 0.55))
        linesPerPage = int((app.height - 120) // app.lineHeight)
        app.charsPerPage = int(charsPerLine * linesPerPage)

        app.pages = makePages(rawText, app.charsPerPage)
        app.totalPages = len(app.pages)
        book.totalPages = app.totalPages

        app.pageIndex = book.currPage

        #when you reopen book pages are reclaulcated and may have elss or more pages,
        #so saved index may be out of range
        app.pageIndex = min(app.pageIndex, app.totalPages - 1)
        app.pageIndex = max(app.pageIndex, 0)

        app.chapters = extractChapters(app.pages)
        app.showChapterPanel = False
        app.chapterScroll = 0


def makeBooks(app):
    bookData = [
        ('The Importance Of Being Earnest', 'Oscar Wilde', 'pg844.cover.medium.jpg', 'pg844.txt'),
        ('Little Women', 'Louisa May Alcott', 'pg26297.cover.medium.jpg', 'pg514.txt'),
        ('The Great Gatsby', 'Scott Fitzgerald','pg64317.cover.medium.jpg', 'pg64317.txt'),
        ('The Scarlet Letter', 'Nathaniel Hawthorne', 'pg25344.cover.medium.jpg', 'pg25344.txt'),
        ('The Tale of Two Cities', 'Charles Dickens', 'pg98.cover.medium.jpg', 'pg98.txt'),
        ('Frankenstein', 'Mary Shelly', 'pg84.cover.medium.jpg', 'pg84.txt'),
        ('The Phantom of the Opera', 'Gaston Leroux', 'pg175.cover.medium.jpg', 'pg175.txt'),
        ('Great Expectations', 'Charles Dickens', 'pg1400.cover.medium.jpg', 'pg1400.txt'),
        ('Autobiography of Benjamin Franklin', 'Benjamin Franklin', 'pg20203.cover.medium.jpg', 'pg20203.txt'),
        ('The Brothers Karamazov', 'Fyodor Dostoyevsky', 'pg28054.cover.medium.jpg', 'pg28054.txt'),
        ('The Count of Monte Cristo', 'Alexandre Dumas', 'pg1184.cover.medium.jpg', 'pg1184.txt'),
        ('Moby Dick; Or, The Whale', 'Herman Melville', 'pg2701.cover.medium.jpg', 'pg2701.txt'),
        ('Romeo and Juliet', 'William Shakespeare', 'pg1513.cover.medium.jpg', 'pg1513.txt'),
        ('Pride and Prejudice', 'Jane Austen', 'pg1342.cover.medium.jpg', 'pg1342.txt'),
        ('Dracula', 'Bram Stoker', 'pg345.cover.medium.jpg', 'pg345.txt')


    ]
    

    for i, (title, author, imageurl, url) in enumerate(bookData):
        app.books.append(Books(i, app, title, author, imageurl, url))



def doNothing():
    pass

def makeButtons(app):
    app.buttons = []

    # ── bottom toolbar (always visible) ──────────────────────────
    def goHome():
        app.defaultScreen, app.libraryScreen, app.readingScreen = True, False, False
    def goLibrary():
        app.defaultScreen, app.readingScreen, app.libraryScreen = False, False, True
    def goContinue():
        if app.currentRead:
            app.defaultScreen = app.libraryScreen = False
            app.readingScreen = True
            makeCurrentBook(app, app.currentRead)
    def toggleFinger():
        app.usingCamera = True
        app.gestureController.start()

    bottomRow = makeButtonRow(
        labels      = ['Home', 'Library', 'Continue', 'Index'],
        onClickFunctions  = [goHome, goLibrary, goContinue, toggleFinger],
        rowCenterY  = app.height - 30,
        totalWidth  = app.width,
        btnHeight   = 40,
        color       = rgb(90, 90, 90),
        hoverColor  = rgb(140, 140, 140),
        fontSize    = 12,
    )
    app.homeButton, app.libraryButton, app.continueReading, app.useFinger = bottomRow
    app.buttons.extend(bottomRow)

    # ── burger-menu column (shown only when burgerPressed) ────────
    menuX   = app.displayScreenLeft + app.displayScreenWidth - app.displayScreenOffsetX - app.menuWidth
    menuTop = app.displayScreenTop  + app.displayScreenOffsetY + app.burgerAndMenuOffset + 30
    spacing = 45
    menuLabels = ['Library', 'Continue', 'Settings']
    menuFunctions    = [goLibrary, goContinue, doNothing]   # settings = TODO

    app.menuButtons = []
    for i, (label, function) in enumerate(zip(menuLabels, menuFunctions)):
        b = Button(menuX, menuTop + i * spacing,
                   app.menuWidth - 2, 35, label, function,
                   color=rgb(40, 40, 40), hoverColor=rgb(80, 80, 80), fontSize=12)
        app.menuButtons.append(b)
        app.buttons.append(b)

    # keep named refs your existing code already uses
    app.settingsButton = app.menuButtons[2]



def onKeyPress(app, key):
    if app.readingScreen:
        if key == 'right' and app.pageIndex < app.totalPages - 1:
            app.pageIndex += 1
            savePageChangeOnKeyPress(app)
        elif key == 'left' and app.pageIndex > 0:
            app.pageIndex -= 1
            savePageChangeOnKeyPress(app)
        elif key == 'c':
            app.showChapterPanel = not app.showChapterPanel
        elif key == 'n':
            app.showNotesPanel = not app.showNotesPanel
            app.showChapterPanel = False 
        elif key == 'b':
            bookmarks = app.currentRead.bookmarks
            if app.pageIndex in bookmarks:
                bookmarks.remove(app.pageIndex)
            else:
                bookmarks.append(app.pageIndex)
            saveAllProgress(app)
        
        elif key == 'up':
            if app.showChapterPanel:
                app.chapterScroll = max(0, app.chapterScroll - 1)
            elif app.showNotesPanel:
                app.notesScroll = max(0, app.notesScroll - 1)
        elif key == 'down':
            
            if app.showChapterPanel:
                maxScroll = max(0, len(app.chapters) - 10)
                app.chapterScroll = min(maxScroll, app.chapterScroll + 1)
            elif app.showNotesPanel:
                totalEntries = len(app.currentRead.bookmarks) + len(app.highlights) + len(app.notes)
                app.notesScroll = min(max(0, totalEntries - 10), app.notesScroll + 1)
        
        elif key == '=':
            app.fontSize = min(24, app.fontSize + 1)
            makeCurrentBook(app, app.currentRead)
        elif key == '-':
            app.fontSize = max(10, app.fontSize - 1)
            makeCurrentBook(app, app.currentRead)



def savePageChangeOnKeyPress(app):
        app.currentRead.saveProgress(app.pageIndex)
        saveAllProgress(app)

def onMousePress(app, mouseX, mouseY):
    checkBurgerPressed(app, mouseX, mouseY)

    for button in app.buttons:
        button.handleClick(mouseX, mouseY)
    if app.readingScreen:
        handleToolbarClick(app, mouseX, mouseY)
        handlePageclick(app, mouseX, mouseY)
    if app.libraryScreen:
        currRead = getBookPressed(app, mouseX, mouseY)
        if currRead is not None:
            app.readingScreen = True  
            app.libraryScreen = False
            app.defaultScreen = False
            makeCurrentBook(app, currRead) 


def onMouseRelease(app, mouseX, mouseY):
    if app.readingScreen and app.activeHighlight and app.highlightStart is not None:


def handleToolbarClick(app, mouseX, mouseY):
    toolbarX = 0
    toolbarWidth = 58
    toolbarTop = 22
    buttonHeight = 70
    gap = 8

    if not (toolbarX <= mouseX <= toolbarWidth):
        return



    highlightY = toolbarTop + gap
    noteY = toolbarTop + gap + (buttonWidth + gap)
    bookmarkY = toolbarTop + gap + 2 * (buttonHeight + gap)

    if toolbarY <= mouseY <= toolbarY + toolbarHeight:
        if highlightX <= mouseX <= highlightX + buttonWidth:
            app.activeHighlight = not app.activeHighlight
            app.activeNote = False
            app.activeBookmark = False
        elif noteY <= mouseY <= noteY + buttonWidth:
            app.activeNote = not app.activeNote
            app.activeHighlight = False
            app.activeBookmark = False
        elif bookmarkY <= mouseY <= bookmarkY + buttonWidth:
            app.activeBookmark = not app.activeBookmark
            app.activeHighlight = False
            app.activeNote = False

def handlePageclick(app, mouseX, mouseY):
    insideBox = (app.bookBoxLeft <= mouseX <= app.bookBoxLeft + app.bookBoxWidth and
                  app.bookBoxTop <= mouseY <= app.bookBoxTop + app.bookBoxHeight - 40)
    if not insideBox:
        return
    pageKey = app.pageIndex
    if app.activeBookmark:
        if pageKey in app.currentRead.bookmarks:
            app.currentRead.bookmarks.remove(pageKey)
        else:
            app.currentRead.bookmarks.append(pageKey)
        saveAllProgress(app)
    
    elif app.activeHighlight:
        charIndex = getCharIndexAtClick(app, mouseX, mouseY)
        if charIndex is not None:
            app.highlightStart = charIndex
    
    elif app.activeNote:
        app.showNotePopup = True
        app.notePopupText = app.notes.get(pageKey, '')
        

def getButtonPressed(app, mouseX, mouseY):
    intersected = []
    for button in app.buttons:
        if button.intersect(mouseX, mouseY):
            intersected.append(button)
    return intersected

def getBookPressed(app, mouseX, mouseY):
    if not app.libraryScreen:
        return None
    for book in app.books:
        if book.intersect(mouseX, mouseY):
            return book
    return None



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
        drawHamburgerButton(app)
        app.useFinger.drawButton()
        
    if app.libraryScreen:
        drawLibraryScreen(app)
        drawHamburgerButton(app)
    #cursor for tracking mediapipe --> drawCircle(app.cursorX, app.cursorY, 10, fill='darkBlue')
    if app.burgerPressed:
        drawBurgerMenu(app)
        drawHamburgerButton(app)

def extractChapters(pages):
    chapters = []
    for pageIndex, pageText in enumerate(pages):
        for line in pageText.split('\n'):
            if looksLikeChapterHeading(line):
                if not chapters or chapters[-1][0] != line.strip():
                    chapters.append((line.strip(), pageIndex))
    return chapters



def looksLikeChapterHeading(line):
    stripped = line.strip()
    if not stripped or len(stripped) > 60:
        return False
    lower = stripped.lower()
    keywords = ['chapter', 'act', 'part', 'book', 'section', 'prologue', 'epilogue']
    for word in keywords:
        if lower.startswith(word):
            return True

    if stripped.isupper() and 3 < len(stripped) < 50:
        return True
    if stripped.endswith('.') and stripped[:-1].isdigit():
        return True
    return False


def drawBook(app):

    drawRect(app.bookBoxLeft, app.bookBoxTop, app.bookBoxWidth, app.bookBoxHeight, fill = 'ivory')
    pageText = app.pages[app.pageIndex]
    drawWrappedText(app, pageText)

    drawLabel(f'Page {app.pageIndex + 1} of {app.totalPages}',
             app.bookBoxLeft + app.bookBoxWidth//2, app.bookBoxTop + app.bookBoxHeight - 15,
             fill = rgb(80,80,80), size = 12)

    if app.pageIndex in app.currentRead.bookmarks:
        drawPolygon(app.bookBoxLeft + app.bookBoxWidth - 24, app.bookBoxTop,
                    app.bookBoxLeft + app.bookBoxWidth, app.bookBoxTop,
                    app.bookBoxLeft + app.bookBoxWidth, app.bookBoxTop + 30,
                    fill = rgb(210,100,70))
        drawLabel('🔖', app.bookBoxLeft + app.bookBoxWidth - 12, app.bookBoxTop + 14, size = 10)

    drawRect(0, 0, app.width, 22, fill = rgb(220, 215, 205))
    drawLabel('C = chapters | N = notes | B = bookmark | < > = turn page',
            app.width//2, 11, fill = rgb(120,120,120), size = 9)

    if app.showChapterPanel:
        drawChapterPanel(app)
    if app.showNotesPanel:
        drawAnnotationsPanel(app)

    drawToolbar(app)
    
def getCharIndexAtClick(app, mouseX, mouseY):
    left = app.bookBoxLeft + app.margin
    right = app.bookBoxLeft + app.bookBoxWidth - app.margin
    maxWidth = right - left
    charsPerLine = int(maxWidth / (app.fontSize * 0.55))
    y = app.bookBoxTop + 30
    charIndex = 0
    text = app.pages[app.pageIndex]

    for paragraph in text.split('\n\n'):
        words = paragraph.split()
        line = ''
        lineStartIndex = charIndex
        for word in words:
            test = line + (' ' if line else '') + word
            if len(test) > charsPerLine:
                lineY = y
                if abs(mouseY - lineY) < app.lineHeight//2:
                    charOffset = int((mouseX - left) / (app.fontSize * 0.55))
                    return lineStartIndex + min(charOffset, len(line))
                y += app.lineHeight
                lineStartIndex = charIndex
                line = word
        else:
            line = test
        charIndex += len(word) + 1

        if line:
            if abs(mouseY - y) < app.lineHeight // 2:
                charOffset = int((mouseX - left) / (app.fontSize * 0.55))
                return lineStartIndex + min(charOffset, len(line))
            y += app.lineHeight
        y += app.lineHeight //2
        charIndex += 2




def drawWrappedText(app, text):
    left = app.bookBoxLeft + app.margin
    right = app.bookBoxLeft + app.bookBoxWidth - app.margin
    maxWidth = right - left
    centerX = left + maxWidth // 2
    charsPerLine = int(maxWidth / (app.fontSize * 0.55))
    y = app.bookBoxTop + 30

    if app.pageIndex in app.highlights:
        drawRect(app.bookBoxLeft, app.bookBoxTop,
                app.bookBoxWidth, app.bookBoxHeight - 40,
                fill = rgb(255, 255, 180), opacity = 40)

    if app.pageIndex in app.notes:
        drawLabel('📝', app.bookBoxLeft + 12, app.bookBoxTop + 12, size=13)

    for paragraph in text.split('\n\n'):
        words = paragraph.split()
        line = ''
        for word in words:
            test = line + (' ' if line else '') + word
            if len(test) > charsPerLine:
                drawLabel(line, centerX, y, align = 'center',
                        size = app.fontSize, fill = 'black')
                y += app.lineHeight
                line = word
                if y > app.bookBoxTop + app.bookBoxHeight - 30:
                    return
            else:
                line = test
        if line:
            
            drawLabel(line, centerX, y, align = 'center',
                    size = app.fontSize, fill='black')
            y += app.lineHeight
        y += app.lineHeight // 2
        if y > app.bookBoxTop + app.bookBoxHeight - 30:
            return

def drawToolbar(app):
    toolbarX = 0
    toolbarWidth = 58
    toolbarTop = 22
    buttonWidth = app.height - 80
    buttonHeight = 70
    gap = 8
    
    drawRect(toolbarX, toolbarTop, toolbarWidth, toolbarHeight, fill = rgb(40,40,40))

    tools = [
        ('🖊','Highlight', 'activeHighlight', rgb(225, 220, 50), rgb(180,150,10)),
        ('📝','Note', 'activeNote', rgb(100, 160, 255), rgb(50,100,200)),
        ('🔖','Bookmark', 'activeBookmarks', rgb(210, 100, 70),  rgb(150,50,30))
    ]

    for i, (icon, label, flag, onColor, pressedColor) in enumerate(tools):
        y = toolbarTop + gap + i * (buttonHeight + gap)
        color = pressedColor if isActive else onColor
        drawRect(toolbarX + 4, y, toolbarWidth - 8, y + buttonHeight, fill = color)
        drawLabel(icon, toolbarX + toolbarWidth//2, y + buttonHeight//2 - 10, size = 16)
        drawLabel(label, toolbarX + toolbarWidth//2, y + buttonHeight//2 + 12, size = 8, fill='white')

def onMouseMove(app, mouseX, mouseY):
    app.cursorX = mouseX
    app.cursorY = mouseY
    for button in app.buttons:
        button.handleHover(mouseX, mouseY)
    
    #BOUND MOUSE MOTIONif app.cursorY
    
def loadBook(filename):
    with open(f'{filename}', 'r', encoding = 'utf-8') as f:
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

def drawLibraryScreen(app):

    defaultScreenURL = 'defaultScreen.png'
    imageWidth, imageHeight = getImageSize(defaultScreenURL)
    drawImage(defaultScreenURL, app.width//2, app.height//2 + 15, align='center', width=imageWidth*1.5, height=imageHeight*1.5)

    turqoise = rgb(188, 221, 212)
    
    lightGray = rgb(226, 226, 226)
    lightGrayBkg = curvedRect(app,app.width//2, app.height//2-15,
                              app.width - 100 - 2*app.displayScreenOffsetX, 
                              app.height - 150 - 2*app.displayScreenOffsetY, 
                              lightGray)
    lightGrayBkg.draw()
    
    darkerTurquoise = rgb(128, 182, 166)
    
    darkerTurquoiseBkg = curvedRect(app,app.width//2, 500, 800, 350, darkerTurquoise)
    darkerTurquoiseBkg.draw()
    darkBlue = rgb(128, 153, 183)
    darkBlueBkg = curvedRect(app,app.width//2, 742, app.width-200, 80, darkBlue)
    darkBlueBkg.draw()
    #DRAW CIRCLES
    Books.drawCovers(app)

def drawDefaultScreen(app):
    defaultScreenURL = 'defaultScreen.png'
    imageWidth, imageHeight = getImageSize(defaultScreenURL)
    drawImage(defaultScreenURL, app.width//2, app.height//2 + 15, align='center', width=imageWidth*1.5, height=imageHeight*1.5)
    

def drawBurgerMenu(app):
    menuX = app.displayScreenLeft + app.displayScreenWidth - app.displayScreenOffsetX - app.menuWidth
    menuTop = app.displayScreenTop + app.displayScreenOffsetY + app.burgerAndMenuOffset
    menuURL = 'menu.png'
    imageWidth, imageHeight = getImageSize(menuURL)
    drawImage(menuURL, menuX - 30, menuTop, width=imageWidth//1.5, height=imageHeight//2)
    for button in app.menuButtons:
        button.draw()

    
def drawHamburgerButton(app):
    hamburgerLineLength = 17
    hamburgerColor = rgb(115, 115, 115)
    spacing = 6
    drawLine(app.displayScreenLeft + app.displayScreenWidth - app.displayScreenOffsetX - hamburgerLineLength, app.displayScreenTop + app.displayScreenOffsetY, app.displayScreenLeft + app.displayScreenWidth - app.displayScreenOffsetX, app.displayScreenTop + app.displayScreenOffsetY, fill = hamburgerColor, lineWidth = 3)
    drawLine(app.displayScreenLeft + app.displayScreenWidth - app.displayScreenOffsetX - hamburgerLineLength, app.displayScreenTop + app.displayScreenOffsetY + spacing, app.displayScreenLeft + app.displayScreenWidth - app.displayScreenOffsetX, app.displayScreenTop + app.displayScreenOffsetY + spacing, fill = hamburgerColor, lineWidth = 3)
    drawLine(app.displayScreenLeft + app.displayScreenWidth - app.displayScreenOffsetX - hamburgerLineLength, app.displayScreenTop + app.displayScreenOffsetY + spacing*2, app.displayScreenLeft + app.displayScreenWidth - app.displayScreenOffsetX, app.displayScreenTop + app.displayScreenOffsetY + spacing*2, fill = hamburgerColor, lineWidth = 3)


def drawChapterPanel(app):
    panelWidth = 195
    panelX = app.bookBoxLeft + app.bookBoxWidth - panelWidth
    panelTop = app.bookBoxTop
    panelHeight = app.bookBoxHeight

    drawRect(panelX, panelTop, panelWidth, panelHeight, fill = rgb(25,25,25), opacity = 93)
    drawLabel('Chapters', panelX + panelWidth//2, panelTop + 18, fill='white', size = 13, bold=True)
    drawLine(panelX, panelTop + 32, panelX + panelWidth, panelTop + 32, fill=rgb(80,80,80))

    lineHeight = 30
    scroll = app.chapterScroll
    maxVisible = (app.height - 80)//lineHeight

    for i, (name, pageIndex) in enumerate(app.chapters[scroll : scroll + maxVisible]):
        y = panelTop + 48 + i * lineHeight
        absIndex = i + scroll

        #AI help with highlighting chapter reader is currently in
        isCurrent = (
            pageIndex <= app.pageIndex and
            (absIndex + 1 >= len(app.chapters) or app.chapters[absIndex + 1][1] > app.pageIndex)
        )
        if isCurrent:
            drawRect(panelX, y - 10, panelWidth, lineHeight, fill=rgb(50,80,60))

        display = name if len(name) <= 26 else name[:23] + '...'
        color = rgb(120,220,160) if isCurrent else 'white'
        drawLabel(display, panelX + 8, y, align = 'left', size = 11, fill = color)
    
    if scroll > 0:
        drawLabel('▲', panelX + panelWidth//2, panelTop + 44, fill = rgb(150,150,150), size = 10)
    if scroll + maxVisible < len(app.chapters):
        drawLabel('▼', panelX + panelWidth//2, panelTop + panelHeight - 15, fill = rgb(150,150,150), size = 10)


def getEntryPage(entry):
    return entry[1]

def drawAnnotationsPanel(app):
    panelWidth = 195
    panelX = app.bookBoxLeft + app.bookBoxWidth - panelWidth
    panelTop = app.bookBoxTop
    panelHeight = app.bookBoxHeight

    drawRect(panelX, panelTop, panelWidth, panelHeight, fill = rgb(20, 20, 40), opacity = 95)
    drawLabel('Bookmarks & Notes', panelX + panelWidth // 2, panelTop + 18,
                fill = 'white', size = 11, bold = True)
    drawLine(panelX, panelTop + 32, panelX + panelWidth, panelTop + 32, fill = rgb(80,80,80))

    lineHeight = 28
    y = panelTop + 44
    scroll = app.notesScroll
    allEntries = []
    
    for pageNum in app.currentRead.bookmarks:
        allEntries.append(('🔖', pageNum, f'Bookmark p.{pageNum + 1}'))
    for pageNum in app.highlights:
        allEntries.append(('🟡', pageNum, f'Highlight p.{pageNum + 1}'))
    for pageNum in app.notes:
        allEntries.append(('📝', pageNum, f'Note p.{pageNum + 1}'))

    allEntries.sort(key = getEntryPage)
    maxVisible = (panelHeight - 60) // lineHeight
    visibleEntries = allEntries[scroll: scroll + maxVisible]

    if not allEntries:
        drawLabel('Nothing saved yet', panelX + panelWidth//2, panelTop + 60,
                fill = rgb(150,150,150), size = 10)
    else:
    
        for icon, pageNum, label in visibleEntries:
            drawLabel(icon + ' ' + label, panelX + 8, y, align = 'left', size = 10, fill = 'white')
            y += lineHeight
    
    if scroll > 0:
        drawLabel('▲', panelX + panelWidth//2, panelTop + 38, fill = rgb(150,150,150), size = 10)
    if scroll + maxVisible < len(allEntries):
        drawLabel('▼', panelX + panelWidth//2, panelTop + panelHeight - 10, fill = rgb(150,150,150), size=10)


class Button:
    def __init__(self, left, top, width, height, text, onClickFunction=None, **kwargs):
        self.left = left
        self.top = top
        self.width = width
        self.height = height
        self.text = text
        self.onClickFunction = onClickFunction

        # Optional styling via **kwargs with sensible defaults
        self.color         = kwargs.get('color', rgb(115, 115, 115))
        self.hoverColor    = kwargs.get('hoverColor', rgb(160, 160, 160))
        self.textColor     = kwargs.get('textColor', 'white')
        self.fontSize      = kwargs.get('fontSize', 13)
        self.bold          = kwargs.get('bold', False)
        self.borderColor   = kwargs.get('borderColor', None)
        self.borderWidth   = kwargs.get('borderWidth', 0)
        self.roundness     = kwargs.get('roundness', 6)   # corner rounding (visual only)
        self.visible       = kwargs.get('visible', True)

        self.isHovered = False

    # ── geometry helpers ──────────────────────────────────────────
    @property
    def centerX(self): return self.left + self.width / 2
    @property
    def centerY(self): return self.top + self.height / 2

    def contains(self, x, y):
        return self.left <= x <= self.left + self.width and \
               self.top  <= y <= self.top  + self.height

    # ── event handlers ────────────────────────────────────────────
    def handleClick(self, mouseX, mouseY):
        if self.visible and self.contains(mouseX, mouseY) and self.onClickFunction:
            self.onClickFunction()

    def handleHover(self, mouseX, mouseY):
        self.isHovered = self.visible and self.contains(mouseX, mouseY)

    # ── drawing ───────────────────────────────────────────────────
    def draw(self):
        if not self.visible:
            return
        fill = self.hoverColor if self.isHovered else self.color

        drawRect(self.left, self.top, self.width, self.height,
                 fill=fill,
                 border=self.borderColor,
                 borderWidth=self.borderWidth)

        drawLabel(self.text, self.centerX, self.centerY,
                  fill=self.textColor,
                  size=self.fontSize,
                  bold=self.bold)

    # ── compatibility with your existing code ─────────────────────
    def intersect(self, x, y):   return self.contains(x, y)
    def drawButton(self):        self.draw()

    def __repr__(self):  return f'Button({self.text!r})'
    def __hash__(self):  return hash(self.text)
    def __eq__(self, other):
        return isinstance(other, Button) and self.text == other.text


# ── layout helper: builds a row of evenly-spaced buttons ──────────
def makeButtonRow(labels, onClickFunctions, rowCenterY, totalWidth,
                  btnHeight=35, padding=10, **kwargs):
    n = len(labels)
    btnWidth = (totalWidth - padding * (n + 1)) / n
    buttons = []
    for i, (label, function) in enumerate(zip(labels, onClickFunctions)):
        left = padding + i * (btnWidth + padding)
        top  = rowCenterY - btnHeight / 2
        buttons.append(Button(left, top, btnWidth, btnHeight, label, function, **kwargs))
    return buttons

class Books:

    def __init__(self, index, app, title, author, imageURL, URL):
        self.shelf = index // app.numBooksPerShelf
        # A book is arranged in a certain order on a shelf based on its index
        self.orderInShelf = index % app.numBooksPerShelf
        shelfStartX = 100
        self.left = shelfStartX + self.orderInShelf * app.bookSpaceX
        self.top = int(app.height*(2/3)) - self.shelf * app.bookSpaceY
        # A book is on shelf 1,2, or 3 based on its index in app.books
        
        self.title = title
        self.URL = URL
        self.bookmarks = []
        self.author = author
        self.coverImage = imageURL
        self.currentlyReading = False
        self.currPage = 0
        self.currentlyOpen = False
        self.totalPages = 0
    
    def saveProgress(self, currPage):      
        self.currPage = currPage

    def loadProgress(self):                
        try:
            with open('progress.txt', 'r') as f:
                for line in f:
                    parts = line.strip().split('|')
                    if len(parts) < 3:
                        continue
                    title, currPage, bookmarks = parts[0], int(parts[1]), parts[2]
                    if self.title == title:
                        self.currPage = currPage
                        self.bookmarks = [int(p) for p in bookmarks.split(',') if p]
        except FileNotFoundError:
            pass

    def getURL(self):
        return self.URL
    
    @staticmethod
    def drawCovers(app):
        for book in app.books:
            imageWidth, imageHeight = getImageSize(book.coverImage)
            drawImage('bookIcon.png', book.left, book.top, align = 'center',
                    width=imageWidth//1.5, height=imageHeight//1.8)
            drawImage(book.coverImage, book.left + 7, book.top - 5, align='center',
                    width=imageWidth//3.5, height=imageHeight//3.5)
            if book.totalPages > 0:
                barW = imageWidth // 2.5
                progress = book.currPage / book.totalPages
                drawRect(book.left - barW//2, book.top + 55, barW, 5, fill = rgb(200,200,200))
                drawRect(book.left - barW//2, book.top + 55, int(barW * progress), 5, fill = rgb(100,180,140))
    
    def intersect(self, x, y):
        imageWidth, imageHeight = getImageSize(self.coverImage)
        width = imageWidth // 3.5
        height = imageHeight // 3.5
        return (self.left - width//2 <= x <= self.left + width//2 and
                self.top - height//2 <= y <= self.top + height//2)

    def __repr__(self):
        return f'book: Author{self.author} Title{self.title}'
    
    def __hash__(self):
        return hash(str(self))
    
    def __eq__(self, other):
        return isinstance(other, Books) and ((self.title, self.author) == (other.title, other.author))
#almost fully integrated gestures classes with AI below but with some self integrated editing:
class GestureModel:
    def __init__(self):
        # Thread safety
        self.lock = threading.Lock()
        
        # Data shared with the background thread
        self.latestLandmark = None
        
        # Public variables for the UI and cursor
        self.swipeDirection = None
        self.swipeDetected = False
        self.fingerScreenX = 200
        self.fingerScreenY = 200
        
        # Swipe detection settings
        self.history = deque()
        self.lastSwipeTime = 0

                # In GestureModel.__init__, change these values:
        self.timeWindow = 0.25       # slightly tighter window
        self.coolDownTime = 1.2      # longer cooldown kills the back-swipe
        self.minVelocity = 250       # raise this — filters out slow drift
        self.swipeThreshold = 50     # larger distance required

    def processLatestLandmark(self):
        """Called by onStep on the Main Thread"""
        with self.lock:
            landmark = self.latestLandmark
            if landmark is None: return
        
        # Index finger tip is landmark index 8
        tip = landmark[8]
        currX, currY = tip.x * 640, tip.y * 480
        currentTime = time.time()

                # Update cursor (0.6/0.4 weighting for smoothness)
        self.fingerScreenX = int(self.fingerScreenX * 0.85 + (tip.x * 680) * 0.15)
        self.fingerScreenY = int(self.fingerScreenY * 0.85 + (tip.y * 890) * 0.15)
        
        # Update history for swipe math
        self.history.append((currentTime, currX, currY))
        while self.history and (currentTime - self.history[0][0] > self.timeWindow):
            self.history.popleft()
            
        # Only detect swipes if we are outside the cooldown period
        if currentTime - self.lastSwipeTime > self.coolDownTime:
            self.detectSwipe(currentTime)

    def detectSwipe(self, currentTime):
        if len(self.history) < 5: return
        
        startTime, startX, startY = self.history[0]
        endTime, endX, endY = self.history[-1]
        
        deltaTime = endTime - startTime
        if deltaTime <= 0: return
        
        diffX = endX - startX
        diffY = endY - startY
        
        # Calculate velocity (pixels per second)
        # This prevents the "undo" move: return movements are usually slower
        velocity = (diffX**2 + diffY**2)**0.5 / deltaTime
        
        if velocity > self.minVelocity:
            # Check if it is primarily horizontal and meets distance threshold
            if abs(diffX) > abs(diffY) and abs(diffX) > self.swipeThreshold:
                self.swipeDirection = "LEFT" if diffX < 0 else "RIGHT"
                self.swipeDetected = True
                self.lastSwipeTime = currentTime
                # Clear history so the return motion isn't processed at all
                self.history.clear()

class GestureController:
    def __init__(self, model):
        self.model = model
        self.isRunning = False
        self.timestamp = 0
        baseOptions = mp.tasks.BaseOptions
        self.options = mp.tasks.vision.HandLandmarkerOptions(
            base_options=baseOptions(model_asset_path='hand_landmarker.task'),
            running_mode=mp.tasks.vision.RunningMode.LIVE_STREAM,
            num_hands=1,
            min_hand_detection_confidence=0.6,
            min_tracking_confidence=0.6,
            result_callback=_gestureCallback
        )

    def start(self):
        if not self.isRunning:
            self.isRunning = True
            threading.Thread(target=self.captureLoop, daemon=True).start()

    def captureLoop(self):
        camera = cv2.VideoCapture(0)
        camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        try:
            handLandmarker = mp.tasks.vision.HandLandmarker
            with handLandmarker.create_from_options(self.options) as landmarker:
                while self.isRunning and camera.isOpened():
                    success, frame = camera.read()
                    if not success: continue
                    frame = cv2.flip(frame, 1)
                    rgbFrame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    mpImage = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgbFrame)
                    self.timestamp += 1
                    landmarker.detect_async(mpImage, self.timestamp)
                    time.sleep(0.01)
        finally:
            camera.release()


class curvedRect:
    def __init__(self, app,cX,cY, width, height, color):
        self.cX = cX
        self.cY = cY
        self.w = width 
        self.h = height 
        self.color=color
    def getLeftTopWidthHeight(self):
        return self.cX, self.cY, self.w, self.h
    def getCircleCoords(self):
        return [(self.cX + 7, self.cY + 8),
                (self.cX +7, self.cY + self.h - 8),
                (self.cX + self.w - 7, self.h + self.cY - 8),
                (self.cX + self.w - 7, self.cY + 8)]
    def draw(self):
        drawRect(self.cX,self.cY,self.w,self.h,fill=self.color,align = 'center')
        
    def drawCircleCoord(self):
        for cx, cy in self.getCircleCoords():
            drawCircle(cx, cy, 10, fill=self.color)

    

def main():
    runApp()

main()
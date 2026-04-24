from cmu_graphics import *
import cv2
import mediapipe as mp
import threading
import time
from collections import deque
global_latest_hand_result = None

#this function completely ai written EXEMPT
def _gestureCallback(result, output_image, timestamp_ms):
    global global_latest_hand_result
    global_latest_hand_result = result

def onAppStart(app):
    

    app.pageIndex = 0
    app.pages = []
    app.totalPages = 0
    app.height = 890
    app.width = 680
    app.readingScreen = False
    app.defaultScreen = True
    app.libraryScreen = False
    app.books = []
    app.currentRead = None
    app.stepsPerSecond = 30

    app.burgerHovered = False



    app.bookSpaceY = 150
    app.numshelves = 3
    app.numBooksPerShelf = 5
    app.bookSpaceX = 105
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
    app.displayScreenOffsetYTurqoise = app.height * 0.825
    app.displayScreenOffsetY = 15
    app.displayScreenOffsetX = 15
    app.displayScreenTop = 90
    app.displayScreenLeft = 88
    app.displayScreenWidth = 490
    app.displayScreenHeight = 650


    app.menuWidth = 115
    app.burgerAndMenuOffset = 22
    app.menuHeight = 130
    app.menuTop = app.displayScreenTop + app.displayScreenOffsetY  + app.burgerAndMenuOffset
    app.menuOpen = False

    app.bookBoxLeft = 60
    app.bookBoxTop = 22
    app.bookBoxWidth = app.width - 60
    app.bookBoxHeight = app.height - 80
    app.margin = 30

    
    app.gestureModel = GestureModel()
    app.gestureController = GestureController(app.gestureModel)

    makeButtons(app)
    makeBooks(app)
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
                    highlightsFile.write(f'{bookTitle}|{pageKey}|{startChar}|{endChar}\n')
    with open('notes.txt', 'w') as notesFile:
        for bookTitle, pageDict in app.allNotes.items():
            for pageKey, noteText in pageDict.items():
                notesFile.write(f'{bookTitle}|{pageKey}|{noteText}\n')

def loadAllProgress(app):
    for book in app.books:
        book.loadProgress()
    try:
        with open('highlights.txt', 'r') as highlightsFile:
            for line in highlightsFile:
                parts = line.strip().split('|')
                if len(parts) == 4:
                    bookTitle = parts[0]
                    pageKey = int(parts[1])
                    startChar = int(parts[2])
                    endChar = int(parts[3])
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
                        app.allNotes[bookTitle] = dict()
                    app.allNotes[bookTitle][pageKey] = noteText
    except FileNotFoundError:
        pass
        

###################################################
#AI for using gesture model
def onStep(app):
    global global_latest_hand_result
    with app.gestureModel.lock:
        if (app.usingCamera and global_latest_hand_result is not None
        and global_latest_hand_result.hand_landmarks):
            app.gestureModel.latestLandmark = global_latest_hand_result.hand_landmarks[0]
        else:
            app.gestureModel.latestLandmark = None
            
    
    # Reset the global variable so we don't process the same frame twice
    global_latest_hand_result = None


    if app.usingCamera and app.gestureModel is not None:
        app.gestureModel.processLatestLandmark(app)
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
    

#some ai for loadbook and makepages for loading pages
def makeCurrentBook(app, book):
    
    app.readingScreen = True
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
    if app.totalPages == 0:
        app.pageIndex = 0
    else:
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



def makeButtons(app):
    app.buttons = []

    def goHome():
        app.defaultScreen, app.libraryScreen, app.readingScreen = True, False, False
    def goLibrary():
        app.defaultScreen, app.readingScreen, app.libraryScreen = False, False, True
    def goContinue():
        if app.currentRead:
            app.defaultScreen = app.libraryScreen = False
            makeCurrentBook(app, app.currentRead)
    #AI used for egsture control lines of toggle finger
    def toggleFinger():
        if app.usingCamera:
            app.usingCamera = False
            app.gestureController.isRunning = False
        else:
            app.usingCamera = True
            app.gestureController.start()

    bottomRow = makeButtonRow(
        labels      = ['Home', 'Library', 'Continue', ''],
        onClickFunctions  = [goHome, goLibrary, goContinue, toggleFinger],
        rowCenterY  = app.height - 30,
        totalWidth  = app.width,
        btnHeight   = 40,
        color       = rgb(90, 90, 90),
        hoverColor  = rgb(140, 140, 140),
        fontSize    = 12,
    )
    app.homeButton, app.libraryButton, app.continueReading, app.useFinger = bottomRow
    app.useFinger.image = 'finger.png'
    app.useFinger.text = ''
    app.useFinger.width = 50
    app.useFinger.height = 50
    app.useFinger.left = app.width - 60
    app.useFinger.top = app.height - 55
    
    app.buttons.extend(bottomRow)
    buttonStartY = app.menuTop + 18
    menuX   = app.displayScreenLeft + app.displayScreenWidth - app.displayScreenOffsetX - app.menuWidth
    spacing = 43
    menuLabels = ['Library', 'Continue']
    menuFunctions    = [goLibrary, goContinue]   # settings = TODO

    app.menuButtons = []
    for i, (label, function) in enumerate(zip(menuLabels, menuFunctions)):
        b = Button(menuX + 2.5, buttonStartY + i * spacing,
                   app.menuWidth - 25, 35, label, function,
                   color=rgb(40, 40, 40), hoverColor=rgb(80, 80, 80), fontSize=12)
        app.menuButtons.append(b)
        app.buttons.append(b)



def onKeyPress(app, key):

    if app.showNotePopup:
        if key == 'enter':
            pageKey = app.pageIndex
            app.notes[pageKey] = app.notePopupText
            app.allNotes[app.currentRead.title] = app.notes
            saveAllProgress(app)

            app.showNotePopup = False
            app.notePopupText = ''
        elif key == 'return':
            app.showNotePopup = False
            app.notePopupText = ''
        elif key == 'delete':
            app.notePopupText = app.notePopupText[:-1]
        elif key == 'space':
            app.notePopupText += ' '
        elif len(key) == 1:
            app.notePopupText += key
        return None
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
                totalEntries = len(app.currentRead.bookmarks) + len(app.notes)
                for pageKey in app.highlights:
                    totalEntries += len(app.highlights[pageKey])
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
    if app.showNotePopup:
        return None
    if app.defaultScreen:
        if 155 <= mouseX <= 525 and 390 <= mouseY <= 680:
            if app.currentRead is None and len(app.books) >0:
                app.currentRead = app.books[0]
            if app.currentRead is not None:
                app.defaultScreen = False
                app.libraryScreen = False
                makeCurrentBook(app, app.currentRead)
                return

    bx1 = app.displayScreenLeft + app.displayScreenWidth - app.displayScreenOffsetX - 17
    bx2 = app.displayScreenLeft + app.displayScreenWidth - app.displayScreenOffsetX
    by1 = app.displayScreenTop + app.displayScreenOffsetY
    by2 = by1 + 12
    if bx1 <= mouseX <= bx2 and by1 <= mouseY <= by2:
        app.menuOpen = not app.menuOpen
        return 
    
    

    for button in app.buttons:
        button.handleClick(mouseX, mouseY)
    if app.readingScreen:
        handleToolbarClick(app, mouseX, mouseY)
        handlePageclick(app, mouseX, mouseY)
        if app.showNotesPanel:
            handleAnnotationsPanelClick(app, mouseX, mouseY)
        if app.showChapterPanel:
            handleChapterPanelClick(app, mouseX, mouseY)
    if app.libraryScreen:
        currRead = getBookPressed(app, mouseX, mouseY)
        if currRead is not None:
            app.libraryScreen = False
            app.defaultScreen = False
            makeCurrentBook(app, currRead) 

    if app.menuOpen:
        menuX = app.displayScreenLeft + app.displayScreenWidth - app.displayScreenOffsetX - app.menuWidth
        menuTop = app.menuTop

        if not (menuX <= mouseX <= menuX + app.menuWidth and
                menuTop <= mouseY <= menuTop + app.menuHeight):
            app.menuOpen = False


#this function is entirely AI written bcs i wanted functionality but ran out of time to write it
def handleChapterPanelClick(app, mouseX, mouseY):
    panelWidth = 165
    panelX = app.bookBoxLeft + app.bookBoxWidth - panelWidth - 10
    panelTop = app.bookBoxTop + 20
    panelHeight = app.bookBoxHeight - 70
    lineHeight = 30

    if not (panelX <= mouseX <= panelX + panelWidth and
            panelTop <= mouseY <= panelTop + panelHeight):
        return

    startY = panelTop + 48
    clickedIndex = (mouseY - startY) // lineHeight + app.chapterScroll

    if 0 <= clickedIndex < len(app.chapters):
        chapterName, pageIndex = app.chapters[int(clickedIndex)]
        app.pageIndex = pageIndex
        app.showChapterPanel = False
        savePageChangeOnKeyPress(app)


def onMouseRelease(app, mouseX, mouseY):
    if app.readingScreen and app.activeHighlight and app.highlightStart is not None:
        endChar = getCharIndexAtClick(app, mouseX, mouseY)
        if endChar is not None and endChar != app.highlightStart:
            pageKey = app.pageIndex
            start = min(app.highlightStart, endChar)
            end = max(app.highlightStart, endChar)
            if pageKey not in app.highlights:
                app.highlights[pageKey] = []
            app.highlights[pageKey].append((start, end))
            app.allHighlights[app.currentRead.title] = app.highlights
            saveAllProgress(app)
        app.highlightStart = None


def handleToolbarClick(app, mouseX, mouseY):
    toolbarTop = 50
    buttonHeight = 55
    gap = 6

    highlightY = toolbarTop + gap
    noteY = toolbarTop + gap + (buttonHeight + gap)
    bookmarkY = toolbarTop + gap + 2 * (buttonHeight + gap)
    if not( 0<= mouseX <=58):
        return None

    if highlightY <= mouseY <= highlightY + buttonHeight:
        app.activeHighlight = not app.activeHighlight
        app.activeNote = False
        app.activeBookmark = False
    elif noteY <= mouseY <= noteY + buttonHeight:
        app.activeNote = not app.activeNote
        app.activeHighlight = False
        app.activeBookmark = False
    elif bookmarkY <= mouseY <= bookmarkY + buttonHeight:
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
        


def getBookPressed(app, mouseX, mouseY):
    if not app.libraryScreen:
        return None
    for book in app.books:
        if book.intersect(mouseX, mouseY):
            return book
    return None

def redrawAll(app):
    
    if app.defaultScreen:
        drawDefaultScreen(app)
        drawHamburgerButton(app)
        
    if app.readingScreen:
        drawBook(app)
        drawHamburgerButton(app)
        app.useFinger.draw()
        
    if app.libraryScreen:
        drawLibraryScreen(app)
        drawHamburgerButton(app)

    if app.menuOpen:
        drawBurgerMenu(app)
        drawHamburgerButton(app)

    if app.showNotePopup:
        drawNotePopup(app)

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

def drawNotePopup(app):
    width, height = 400, 200
    cx, cy = app.width //2, app.height //2
    drawRect(cx - width//2, cy - height//2, width, height, fill='white', border='black')
    drawLabel("Write Note:", cx, cy - 70, size=16, bold=True)
    drawLabel(app.notePopupText, cx, cy, size=12)
    drawLabel("Press RETURN to save | ESC to cancel", cx, cy + 70, size=10, fill='gray')



def drawBook(app):
    if app.totalPages == 0:
        drawLabel('No pages loaded', app.width //2, app.height //2,size=20 )
        return None


    turqoise = rgb(188, 221, 212)
    drawRect(0,0, app.width,app.height,fill=turqoise)
    drawRect(app.width//2, app.height//2 + 20, app.bookBoxWidth + 50, app.bookBoxHeight + 40, fill = 'ivory',align='center')
    pageText = app.pages[app.pageIndex]
    drawWrappedText(app, pageText)

    drawLabel(f'Page {app.pageIndex + 1} of {app.totalPages}',
             app.bookBoxLeft + app.bookBoxWidth//2, app.bookBoxTop + app.bookBoxHeight - 15,
             fill = rgb(80,80,80), size = 12)

    if app.pageIndex in app.currentRead.bookmarks:
        bookmarkTop = app.height//2 + 20 - (app.bookBoxHeight +40)//2
        bookmarkRight = app.width//2 + (app.bookBoxWidth +50)//2

        drawPolygon(bookmarkRight - 28, bookmarkTop,
                    bookmarkRight, bookmarkTop,bookmarkRight, bookmarkTop + 36,
                    fill = rgb(210,100,70))

    drawRect(0, 0, app.width, 42, fill=rgb(245, 240, 230))
    drawLabel('C = chapters | N = notes | B = bookmark | < > = turn page',
            app.width//2, 21, fill =rgb(80, 80, 80), size = 21, bold = True)
    if app.activeHighlight:
        drawLabel('Highlight mode ON',app.width//2, 55, size=12, bold=True, fill=rgb(90,90,90))
    elif app.activeNote:
        drawLabel('Highlight mode ON',app.width//2, 55, size=12, bold=True, fill=rgb(90,90,90))
    elif app.activeBookmark:
        drawLabel('Bookmark mode ON',app.width//2, 55, size=12, bold=True, fill=rgb(90,90,90))

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

def drawHighlight(app, text):
    if app.pageIndex not in app.highlights:
        return None
    left = app.bookBoxLeft + app.margin
    right = app.bookBoxLeft + app.bookBoxWidth - app.margin
    maxWidth = right - left
    centerX = left + maxWidth //2
    charsPerLine = int(maxWidth / (app.fontSize * 0.55))
    charWidth = app.fontSize * 0.55
    y = app.bookBoxTop + 45
    charIndex = 0
    ranges = app.highlights[app.pageIndex]

    for paragraph in text.split('\n\n'):
        words = paragraph.split()
        line = ''
        lineStartIndex = charIndex


        for word in words:
            test = line + (' ' if line else '') + word
            if len(test) > charsPerLine:
                for startChar, endChar in ranges:
                    overlapStart = max(startChar, lineStartIndex)
                    overlapEnd = min(endChar, lineStartIndex + len(line))
                    pixelX = centerX - (len(line) * charWidth) // 2 + (overlapStart - lineStartIndex) * charWidth
                    pixelWidth = (overlapEnd - overlapStart) * charWidth
                    if overlapStart < overlapEnd:
                        
                        drawRect(pixelX, y - app.lineHeight //2, pixelWidth, app.lineHeight, fill = rgb(255, 240, 80), opacity = 60)
                y += app.lineHeight
                lineStartIndex = charIndex
                line = word

            else:
                line = test
            charIndex += len(word) + 1
        
        if line:
            for startChar, endChar in ranges:
                overlapStart = max(startChar, lineStartIndex)
                overlapEnd = min(endChar, lineStartIndex + len(line))
                pixelX = centerX - (len(line) * charWidth) // 2 + (overlapStart - lineStartIndex) * charWidth
                pixelWidth = (overlapEnd - overlapStart) * charWidth
                if overlapStart < overlapEnd:
                    drawRect(pixelX, y - app.lineHeight // 2, pixelWidth,
                            app.lineHeight, fill = rgb(255, 240, 80),
                            opacity = 60)
            y += app.lineHeight
        y += app.lineHeight // 2
        charIndex += 2



def drawWrappedText(app, text):
    left = app.bookBoxLeft + app.margin
    right = app.bookBoxLeft + app.bookBoxWidth - app.margin
    maxWidth = right - left
    centerX = left + maxWidth // 2
    charsPerLine = int(maxWidth / (app.fontSize * 0.55))
    y = app.bookBoxTop + 45
    drawHighlight(app,text)
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
    toolbarTop = 50
    buttonHeight = 55
    gap = 6
    toolbarHeight = gap + 3* (buttonHeight + gap)
    
    darkGray = rgb(240, 240, 240)
    drawRect(toolbarX, toolbarTop, toolbarWidth, toolbarHeight, fill = darkGray, opacity = 80)
    drawRect(toolbarX, toolbarTop, toolbarWidth, toolbarHeight,
         fill=darkGray, border=rgb(210,210,210))
    highlightLight = rgb(250, 230,150 )
    highlightDark = rgb(224, 199, 105)

    noteLight = rgb(180, 200, 230)
    noteDark = rgb(140, 165, 200)
    #I asked AI to find rgb values for slightly darker ver of colors above 
    bookmarkLight = rgb(240, 180, 190)
    bookmarkDark = rgb(210, 140, 150)
    tools = [
        ('highlight.jpg','Highlight', 'activeHighlight', highlightLight, highlightDark),
        ('note.jpg','Note', 'activeNote', noteLight, noteDark),
        ('bookmark.jpg','Bookmark', 'activeBookmark', bookmarkLight,  bookmarkDark)
    ]

    for i, (icon, label, flag, onColor, pressedColor) in enumerate(tools):
        y = toolbarTop + gap + i * (buttonHeight + gap)
        if flag == 'activeHighlight':
            isActive = app.activeHighlight
        elif flag == 'activeNote':
            isActive = app.activeNote
        else:
            isActive = app.activeBookmark
        color = pressedColor if isActive else onColor
        drawRect(toolbarX + 4, y, toolbarWidth - 8, buttonHeight, fill = color)

        iconSize = 55
        drawImage(icon, toolbarX + toolbarWidth//2, y + buttonHeight//2,
                width=iconSize, height=iconSize, align='center')
            
def onMouseMove(app, mouseX, mouseY):
    app.cursorX = mouseX
    app.cursorY = mouseY
    for button in app.buttons:
        button.handleHover(mouseX, mouseY)


    
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

    
    turqoise = rgb(188, 221, 212)
    drawRect(0, 0, app.width, app.height, fill=turqoise)
    
    lightGray = rgb(226, 226, 226)
    lightGrayBkg = curvedRect(app,app.width//2, app.height//2-15,
                              app.width - 100 - 2*app.displayScreenOffsetX, 
                              app.height - 150 - 2*app.displayScreenOffsetY, 
                              lightGray)
    lightGrayBkg.draw()
    
    #draw shelves used ai to find correct adjustment for width and heigh to make match books
    shelfURL = 'shelf.png'
    drawImage(shelfURL, app.width//2, 510,
              width=560, height=500,
              align='center')



    Books.drawCovers(app)

def drawDefaultScreen(app):
    defaultScreenURL = 'defaultScreen.png'
    imageWidth, imageHeight = getImageSize(defaultScreenURL)
    drawImage(defaultScreenURL, app.width//2, app.height//2 +20, align='center', width=imageWidth*0.7, height=imageHeight*0.7)
    drawImage('CuteIcon.png', 170, 180, width = 190, height = 190, align='center')
    

def drawBurgerMenu(app):
    menuX = app.displayScreenLeft + app.displayScreenWidth - app.displayScreenOffsetX - app.menuWidth
    menuTop = app.menuTop
    menuURL = 'menu.png'
    imageWidth, imageHeight = getImageSize(menuURL)
    drawImage(menuURL, menuX - 15, menuTop, width=125, height=125)
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
    panelTop = app.bookBoxTop + 20
    panelHeight = app.bookBoxHeight - 70

    drawRect(panelX, panelTop, panelWidth, panelHeight, fill = rgb(25,25,25), opacity = 93)
    drawLabel('Chapters', panelX + panelWidth//2, panelTop + 18, fill='white', size = 13, bold=True)
    drawLine(panelX, panelTop + 32, panelX + panelWidth, panelTop + 32, fill=rgb(80,80,80))

    lineHeight = 30
    scroll = app.chapterScroll
    maxVisible = (panelHeight - 80)//lineHeight

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

        #AI written display var bcs last minute implementation

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
                fill = rgb(50,50,50), size = 11, bold = True)
    drawLine(panelX, panelTop + 32, panelX + panelWidth, panelTop + 32, fill = rgb(80,80,80))

    lineHeight = 28
    y = panelTop + 44
    scroll = app.notesScroll
    allEntries = []
    for pageKey, rangeList in app.highlights.items():
        for startChar, endChar in rangeList:
            if pageKey < len(app.pages):
                snippet = app.pages[pageKey][int(startChar):int(endChar)]
                snippet = snippet.replace('\n', ' ')
                if len(snippet) > 28:
                    snippet = snippet[:28] + '...'
                allEntries.append(('🟡', pageKey, snippet))
    
    for pageKey, noteText in app.notes.items():
        preview = noteText[:28] + '...' if len(noteText) > 28 else noteText
        allEntries.append(('📝', pageKey, preview))
    
    for pageNum in app.currentRead.bookmarks:
        allEntries.append(('🔖', pageNum, f'Bookmark p.{pageNum + 1}'))

    allEntries.sort(key = getEntryPage)
    maxVisible = (panelHeight - 60) // lineHeight
    visibleEntries = allEntries[scroll: scroll + maxVisible]

    if not allEntries:
        drawLabel('Nothing saved yet', panelX + panelWidth//2, panelTop + 60,
                fill = rgb(150,150,150), size = 10)
    else:
    
        for icon, pageNum, label in visibleEntries:
            drawLabel(icon + ' ' + label, panelX + 8, y, align = 'left', size = 10, fill = 'white')
            drawLabel('x', panelX + panelWidth - 12, y, align = 'left', size = 18,bold=True, fill = rgb(180, 80, 80))
            y += lineHeight
    
    if scroll > 0:
        drawLabel('▲', panelX + panelWidth//2, panelTop + 38, fill = rgb(150,150,150), size = 10)
    if scroll + maxVisible < len(allEntries):
        drawLabel('▼', panelX + panelWidth//2, panelTop + panelHeight - 10, fill = rgb(150,150,150), size=10)


def handleAnnotationsPanelClick(app, mouseX, mouseY):
    panelWidth = 195
    panelX = app.bookBoxLeft + app.bookBoxWidth - panelWidth
    panelTop = app.bookBoxTop
    panelHeight = app.bookBoxHeight
    lineHeight = 28
    scroll = app.notesScroll
    maxVisible = (panelHeight - 60) // lineHeight

    if not (panelX <= mouseX <= panelX + panelWidth):
        return None
    
    allEntries = []
    for pageNum in app.currentRead.bookmarks:
        allEntries.append(('🔖', pageNum, f'Bookmark p.{pageNum + 1}'))
    for pageKey, rangeList in app.highlights.items():
        for startChar, endChar in rangeList:
            if pageKey < len(app.pages):
                snippet = app.pages[pageKey][int(startChar):int(endChar)].replace('\n', ' ')
                if len(snippet) > 28:
                    snippet = snippet[:28] + '...'
                allEntries.append(('🟡', pageKey, snippet))
    for pageKey, noteText in app.notes.items():
        preview = noteText[:28] + '...' if len(noteText) > 28 else noteText
        allEntries.append(('📝', pageKey, preview))
    
    allEntries.sort(key = getEntryPage)
    visibleEntries = allEntries[scroll: scroll + maxVisible]

    deleteCenterX = panelX + panelWidth - 12
    deleteRadius = 16

    for i, (icon, pageKey, label) in enumerate(visibleEntries):
        entryY = panelTop + 44 + i * lineHeight
        if entryY <= mouseY <= entryY + lineHeight:  
                if (deleteCenterX - deleteRadius) <= mouseX <= deleteCenterX + deleteRadius and (entryY - 10 <= mouseY <= entryY + 10):
                    if icon == '🟡':
                        newRanges = []
                        removedOne = False
                        for startChar, endChar in app.highlights[pageKey]:
                            #used AI to get snippet code
                            snippet = app.pages[pageKey][int(startChar):int(endChar)].replace('\n', ' ')
                            if len(snippet) > 28:
                                snippet = snippet[:28] + '...'
                            if snippet == label and removedOne == False:
                                removedOne = True
                            else:
                                newRanges.append((startChar, endChar))
                        app.highlights[pageKey] = newRanges
                        app.allHighlights[app.currentRead.title] = app.highlights
                    elif icon == '📝':
                        app.notes = {k: v for k, v in app.notes.items() if k != pageKey }
                        app.allNotes[app.currentRead.title] = app.notes
                    elif icon == '🔖':
                        if pageKey in app.currentRead.bookmarks:
                            app.currentRead.bookmarks.remove(pageKey)
                    saveAllProgress(app)
                else:
                    app.pageIndex = pageKey
                    app.showNotesPanel = False
                    savePageChangeOnKeyPress(app)
                return

#from lauren's post on ED

class Button:
    def __init__(self, left, top, width, height, text, onClickFunction=None, **kwargs):
        self.left = left
        self.top = top
        self.width = width
        self.height = height
        self.text = text
        self.image = kwargs.get('image', None)
        self.onClickFunction = onClickFunction

        #  styling using **kwargs with default valkues
        self.color         = kwargs.get('color', rgb(115, 115, 115))
        self.hoverColor    = kwargs.get('hoverColor', rgb(160, 160, 160))
        self.textColor     = kwargs.get('textColor', 'white')
        self.fontSize      = kwargs.get('fontSize', 13)
        self.bold          = kwargs.get('bold', False)
        self.borderColor   = kwargs.get('borderColor', None)
        self.borderWidth   = kwargs.get('borderWidth', 0)
        self.roundness     = kwargs.get('roundness', 6)  
        self.visible       = kwargs.get('visible', True)

        self.isHovered = False

    @property
    def centerX(self): return self.left + self.width / 2
    @property
    def centerY(self): return self.top + self.height / 2

    def contains(self, x, y):
        return self.left <= x <= self.left + self.width and \
               self.top  <= y <= self.top  + self.height

    def handleClick(self, mouseX, mouseY):
        if self.visible and self.contains(mouseX, mouseY) and self.onClickFunction:
            self.onClickFunction()

    def handleHover(self, mouseX, mouseY):
        self.isHovered = self.visible and self.contains(mouseX, mouseY)

    # AI used to help debug draw function so aspects done by AI for adjustments
    def draw(self):
        if self.image is not None:
            drawImage(self.image, self.centerX, self.centerY,
                    width=self.height * 0.8,
                    height=self.height * 0.8,
                    align='center')
        else:
            drawRect(self.left, self.top, self.width, self.height,
                    fill=self.hoverColor if self.isHovered else self.color)
            
            drawLabel(self.text, self.centerX, self.centerY,
                    fill=self.textColor,
                    size=self.fontSize,
                    bold=self.bold)

    def intersect(self, x, y):   return self.contains(x, y)
    def drawButton(self):        self.draw()

    def __repr__(self):  return f'Button({self.text!r})'
    def __hash__(self):  return hash(self.text)
    def __eq__(self, other):
        return isinstance(other, Button) and self.text == other.text

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
        shelfYValues = [640, 465, 288]
        imageWidth, imageHeight = getImageSize(imageURL)
        bookIconHeight = imageHeight // 2.8
        self.top = shelfYValues[self.shelf] - bookIconHeight/2

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
                    if len(parts) < 4:
                        continue
                    title, currPage, bookmarks = parts[1], int(parts[2]), parts[3]
                    if self.title == title:
                        self.currPage = int(currPage)
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
                    width=imageWidth//2.4, height=imageHeight//2.8)
            drawImage(book.coverImage, book.left + 7, book.top - 5, align='center',
                    width=imageWidth//5.2, height=imageHeight//5.2)
            if book.totalPages > 0:
                barW = imageWidth // 2.5
                progress = book.currPage / book.totalPages
                drawRect(book.left - barW//2, book.top + 55, barW, 5, fill = rgb(200,200,200))
                progressWidth = int(barW * progress)
                if progressWidth > 0:
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

    def processLatestLandmark(self, app):
        with self.lock:
            landmark = self.latestLandmark
            if landmark is None: return
        
        # Index finger tip is landmark index 8
        tip = landmark[8]
        currX, currY = tip.x * 640, tip.y * 480
        currentTime = time.time()

                # Update cursor (0.6/0.4 weighting for smoothness)
        self.fingerScreenX = int(self.fingerScreenX * 0.85 + tip.x * app.width * 0.15)
        self.fingerScreenY = int(self.fingerScreenY * 0.85 + tip.y * app.height * 0.15)
        
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
        
        velocity = (diffX**2 + diffY**2)**0.5 / deltaTime
        
        if velocity > self.minVelocity:
            # Check if it is primarily horizontal and meets distance threshold
            if abs(diffX) > abs(diffY) and abs(diffX) > self.swipeThreshold:
                self.swipeDirection = "LEFT" if diffX < 0 else "RIGHT"
                self.swipeDetected = True
                self.lastSwipeTime = currentTime
                # Clear history so the return motion isn't processed at all
                self.history = deque(maxlen=10)

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

    def getCircleCoords(self):
        left = self.cX - self.w // 2
        right = self.cX + self.w // 2
        bottom = self.cY + self.h // 2
        top = self.cY - self.h // 2
        return [(left + 7, top + 8),
                (left + 7, bottom - 8),
                (right - 7, bottom - 8),
                (right - 7, top + 8)]
    def draw(self):
        drawRect(self.cX,self.cY,self.w,self.h,fill=self.color,align = 'center')
        for x,y in self.getCircleCoords():
            drawCircle(x, y, 7, fill = self.color)
        
    

def main():
    runApp()

main()
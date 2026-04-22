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
#0.25 srconds compatrtp location 0.25 srconds ago if large eough shange page
# #zooming and saving ppages amd ignor eswpies for 0.5 seconds
#make sure works smoothly
#start by debouncing to infinity
    app.gestureModel = GestureModel()
    app.gestureController = GestureController(app.gestureModel)
    app.usingCamera = False
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
    makeButtons(app)
    makeBooks(app)
    app.gestureModel = GestureModel()
    app.gestureController = GestureController(app.gestureModel)


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
            elif swipeDir == "RIGHT" and app.pageIndex > 0:
                app.pageIndex -= 1
        
        # 3. If a swipe happened on a non-reading screen, reset it so it 
        # doesn't 'carry over' when the user eventually opens a book.
        elif app.gestureModel.swipeDetected:
            app.gestureModel.swipeDetected = False
    # If not using camera, onMouseMove handles app.cursorX/Y automatically
    



#some ai for loadbook and makepages for loading pages
def makeCurrentBook(app, book):
    
    if app.readingScreen:
        app.currentRead = book
        app.margin = 30
        app.lineHeight = 18
        app.fontSize = 14
        app.fileName =  book.getURL()
        rawText = loadBook(app.fileName)
        charsPerLine = (app.width - 2 * app.margin) // (app.fontSize * 0.6)
        linesPerPage = (app.height - 120) // app.lineHeight
        app.charsPerPage = int(charsPerLine * linesPerPage)
        app.pages = makePages(rawText, app.charsPerPage)
        app.pageIndex = 0
        app.totalPages = len(app.pages)


def makeBooks(app):
    app.earnestWilde = Books(100, 400, 'The Importance Of Being Earnest', 'Oscar Wilde', 254, 'pg844.cover.medium.jpg', 'pg844.txt')
    app.books.append(app.earnestWilde)
    app.littleWomenAlcott = Books(225, 400, 'Little Women', 'Louisa May Alcott', 499, 'pg26297.cover.medium.jpg', 'pg514.txt')
    app.books.append(app.littleWomenAlcott)
    app.gatsbyFitzgerald = Books(350, 400, 'The Great Gatsby', 'Scott Fitzgerald', 180, 'pg64317.cover.medium.jpg', 'pg64317.txt')
    app.books.append(app.gatsbyFitzgerald)
    app.scarletHawthorne = Books(100, 550, 'The Scarlet Letter', 'Nathaniel Hawthorne', 272,'pg25344.cover.medium.jpg', 'pg25344.txt')
    app.books.append(app.scarletHawthorne)


def makeButtons(app):
    app.buttons = []
    darkPastelBlue = rgb(115, 115, 115)
    buttonsSpacingInMenu = 50
    app.libraryButton = Buttons(app.displayScreenLeft + app.displayScreenWidth - app.displayScreenOffsetX- app.menuWidth,
                                app.displayScreenTop + app.displayScreenOffsetY + app.burgerAndMenuOffset, 
                                app.menuWidth - 2.5, app.menuHeight//4,
                                'white', darkPastelBlue, 'Library', None )
    app.buttons.append(app.libraryButton)
    app.continueReading = Buttons(app.displayScreenLeft + app.displayScreenWidth - app.displayScreenOffsetX - app.menuWidth,
                                app.displayScreenTop + app.displayScreenOffsetY + app.burgerAndMenuOffset + buttonsSpacingInMenu, 
                                app.menuWidth - 2.5, app.menuHeight//4,
                                'white', darkPastelBlue, 'continue Reading', None)
    app.buttons.append(app.continueReading)
    app.useFinger = Buttons(app.displayScreenLeft + app.displayScreenWidth - app.displayScreenOffsetX - app.menuWidth,
                                app.height - 50, 
                                app.menuWidth - 2.5, app.menuHeight//4,
                                'white', darkPastelBlue, 'finger', None)
    app.buttons.append(app.useFinger)

def onKeyPress(app, key):
    if app.readingScreen:
        if key == 'right' and app.pageIndex < app.totalPages - 1:
            app.pageIndex += 1
        elif key == 'left' and app.pageIndex > 0:
            app.pageIndex -= 1

def onMousePress(app, mouseX, mouseY):
    print(f"bookClicked={getBookPressed(app, mouseX, mouseY)}")
    checkBurgerPressed(app, mouseX, mouseY)
    
    if app.libraryButton in getButtonPressed(app, mouseX, mouseY):
        app.defaultScreen = False
        app.readingScreen = False
        app.libraryScreen = True
    
    if app.continueReading in getButtonPressed(app, mouseX, mouseY):
        if app.currentRead is not None:
            app.libraryScreen = False
            app.defaultScreen = False
            app.readingScreen = True
            makeCurrentBook(app, app.currentRead)
    
    if app.useFinger in getButtonPressed(app, mouseX, mouseY):
        app.usingCamera = True
        app.gestureController.start()
    
    currRead = getBookPressed(app, mouseX, mouseY)
    if currRead is not None and app.libraryScreen:
        app.readingScreen = True    # set FIRST
        app.libraryScreen = False
        app.defaultScreen = False
        makeCurrentBook(app, currRead)  # called SECOND, after readingScreen is True

def getButtonPressed(app, mouseX, mouseY):
    intersected = []
    for button in app.buttons:
        if button.intersect(mouseX, mouseY):
            intersected.append(button)
    return intersected

def getBookPressed(app, mouseX, mouseY):
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
        app.useFinger.drawButton()
        
    if app.libraryScreen:
        drawLibraryScreen(app)
    #cursor for tracking mediapipe --> drawCircle(app.cursorX, app.cursorY, 10, fill='darkBlue')
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

def drawLibraryScreen(app):
    Books.drawCovers(app)


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
    app.continueReading.drawButton()
    
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
            drawLabel(self.text, self.left + self.width//2, self.top + self.height//2, fill=self.textColor)
        else:
            raise Exception("Haven't set button size and position yet before drawing")
    
    def __hash__(self):
        return hash(str(self))
    
    def __eq__(self, other):
        return isinstance(other, Buttons) and (self.text, self.backgroundColor, self.textColor) == (other.text, other.backgroundColor, other.textColor)

class Books:
    def __init__(self, left, top, title, author, numPages, imageURL, URL):
        self.left = left
        self.top = top
        self.title = title
        self.URL = URL
        self.author = author
        self.coverImage = imageURL
        self.numPages = numPages
        self.currentlyReading = False
        self.currPage = 0
        self.currentlyOpen = False

    def getURL(self):
        return self.URL
    
    @staticmethod
    def drawCovers(app):
        for book in app.books:
            imageWidth, imageHeight = getImageSize(book.coverImage)
            drawImage('bookIcon.png', book.left + 5, book.top + 5, align = 'center',
                    width=imageWidth//1.7, height=imageHeight//1.7)
            drawImage(book.coverImage, book.left, book.top, align='center',
                    width=imageWidth//2, height=imageHeight//2)
    
    def intersect(self, x, y):
        imageWidth, imageHeight = getImageSize(self.coverImage)
        halfW = imageWidth // 4
        halfH = imageHeight // 4
        return (self.left - halfW <= x <= self.left + halfW and
                self.top - halfH <= y <= self.top + halfH)

    def __repr__(self):
        return f'book: Author{self.author} Title{self.title}'
    
    def __hash__(self):
        return hash(str(self))
    
    def __eq__(self, other):
        return isinstance(other, Books) and ((self.title, self.author) == (other.title, other.author))

##########################################################################
#almost fully integrated gestures with AI below but with some self integrated codeclass GestureModel:
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
def main():
    runApp()

main()
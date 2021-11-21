from multiprocessing import Process,  Pipe
from pdfminer.pdfpage import PDFPage
from pdfminer.layout import LAParams
from pdfminer.converter import TextConverter
import tkinter as tk
from tkinter import filedialog
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from io import StringIO
import os
import time
import pickle
import re
import nltk


class Controller:
    def __init__(self):
        self.filename = ''
        self.isCsv = True
        self.var = 0
        self.isDir = False
        self.txtbox = 0
        self.count = 0
        self.prediction = ''
        self.process1 = 9512
        self.fcount = 0
        self.done = False
        self.pro = []
        self.main, self.proc = Pipe()
        self.filelist = []
        pickle_in = open("prob.pkl", "rb")
        self.classifier = pickle.load(pickle_in)

    def browseFiles(self):
        self.filename = filedialog.askopenfilename(initialdir="./", title="Select a Document",
                                                   filetypes=(("Pdf files", "*.pdf"), ("Text files", "*.txt*")))
        self.isDir = False

        self.txtbox.delete("1.0", "end")
        self.txtbox.insert("1.0", "Selected File is:\n\n" +
                           self.filename+"\n\n Press Start! to start processing")
        self.prediction = ''
        self.process1 = 9512
        self.done = False

    def browseDir(self):
        self.filename = filedialog.askdirectory(
            initialdir="./", title="Select a Directory which contains Annul Report")
        self.isDir = True
        self.txtbox.delete("1.0", "end")
        self.txtbox.insert("1.0", "Selected Directory is:\n\n" +
                           self.filename+"\n\n- Only files of .pdf and .txt are selected(If available)\n\n Press Start! to start processing")
        self.prediction = ''
        self.process1 = 9512
        self.done = False
        self.file = ''
        self.filelist = []
        self.fcount = 0

    def csvorxl(self):
        temp = self.var.get()
        if(temp == 1):
            self.isCsv = True
        else:
            self.isCsv = False

    def convert_pdf_to_str(self, path):
        rsrcmgr = PDFResourceManager()
        retstr = StringIO()
        codec = 'utf-8'
        laparams = LAParams()
        device = TextConverter(rsrcmgr, retstr, laparams=laparams)
        fp = open(path, 'rb')
        interpreter = PDFPageInterpreter(rsrcmgr, device)
        password = ""
        maxpages = 0
        caching = True
        pagenos = set()

        for page in PDFPage.get_pages(fp, pagenos, maxpages=maxpages, password=password, caching=caching, check_extractable=True):
            interpreter.process_page(page)

        text = retstr.getvalue()

        fp.close()
        device.close()
        retstr.close()
        return text

    def convert_txt_to_str(self, path):
        file1 = open(path, "r+")
        return(file1.read())

    def process(self, file, sender, dir):
        print("A process created for:" + file)
        start = time.time()
        text = ''
        if(file[-1] == 'f'):
            text = self.convert_pdf_to_str(file)
        else:
            text = self.convert_txt_to_str(file)
        text = str(text)
        text = re.sub('\s+', ' ', text)

        a = set(nltk.corpus.stopwords.words('english'))

        text1 = nltk.word_tokenize(text.lower())
        stopwords = [x for x in text1 if x not in a]
        text = nltk.word_tokenize(" ".join(map(str, stopwords)))
        finaltext = ''

        for token in text:
            if(nltk.pos_tag([token])[0][1] == 'JJ' or nltk.pos_tag([token])[0][1] == 'NN' or nltk.pos_tag([token])[0][1][0] == 'V'):
                finaltext += " "+nltk.pos_tag([token])[0][0]

        prediction = self.classifier.predict_proba([finaltext])
        if(dir):
            li = []
            for x in prediction[0]:
                li.append(x)
            goals = ['No Poverty', 'Zero Hunger', 'Good Health and Well-Being',
                     'Quality Education', 'Gender Equality', 'Clean Water And Sanitation', 'Affordable Clean Energy',
                     'Decent Work And Economic Growth', 'Industry,Innovation And Infrastructure', 'Reduced Inqualities',
                     'Sustainable Cities And Communities', 'Responsible Consumption And Production', 'Climate Action', 'Life Below Earth', 'Life on Land']
            final = ''
            count = 0
            temp1 = ""
            temp2 = ""
            temp3 = "-"
            final += "\n\t"+temp3*83+"\n\t"
            li1 = li.copy()
            li1.sort(reverse=True)
            for x in li1:
                temp = li.index(x)
                temp1 = str(temp+1)
                if(temp < 9):
                    temp1 = "0"+str(temp+1)
                temp2 = str(count+1)
                if(count < 9):
                    temp2 = "0"+str(count+1)
                temp3 = ' '
                final += "|"+temp2+". "+temp1+" - " + \
                    str(goals[temp])+temp3 * \
                    (40-len(goals[temp]))+"=>\t"+str(x) + \
                    temp3*(30-len(str(x)))+"|\n\t"

                temp3 = '-'
                final += temp3*83+"\n\t"
                count += 1
            final += "\t\t\t\t\t\t\tTime Elapsed:" + \
                str(round(time.time()-start, 2))+" Seconds"
            sender.send([file, final])

            sender.close()
            return
        sender.send([file, prediction[0]])
        sender.close()

    def control(self):
        if(self.filename == ""):

            self.txtbox.delete("1.0", "end")
            self.txtbox.insert("1.0", "!!!Select A File!!!")
            return
        if(self.done):
            if(not self.isDir):
                self.txtbox.delete("1.0", "end")
                self.prediction = self.main.recv()
                self.txtbox.insert(
                    "1.0", "\t\t\t\t\t**Rankings**\n\t\t\t File Path: "+self.prediction[0]+self.prediction[1])

                self.prediction = ''
                self.process1 = 9512
                self.done = False
                return
            else:  # For Directories
                self.fcount += 1
                self.done = False
                self.process1 = 9512
                self.prediction = self.main.recv()
                if(self.isCsv):  # For CSVs
                    temp1 = ""
                    temp2 = ""

                    temp1 = self.prediction[0].split('/')[-1]
                    for x in self.prediction[1]:
                        temp2 += str(x)+","
                    self.file.write(temp1+","+temp2+"\n")
                    self.root.after(250, self.control)
                return
        steps = ["⢿", "⣻", "⣽", "⣾", "⣷", "⣯", "⣟", "⡿"]
        temp = ""
        if(self.isDir):
            if(self.process1 != 9512):

                self.count += 1
                self.count %= 8
                self.txtbox.delete("1.0", "end")
                self.txtbox.insert(
                    "1.0", "\n\n\n\n\n\n\n\n\n\n\n \t\t\t\t\t"+steps[self.count]+" Processing "+steps[self.count]+"\n\n \t\t\t"+"Processed "+str(self.fcount+1)+" Out Of "+str(len(self.filelist))+"\n\n\n\t\t\t\t\t Estimated Time To Complete(Sec): "+str((len(self.filelist) - self.fcount+1)*60))
                self.root.after(250, self.control)

                if(not self.process1.is_alive()):
                    self.done = True

                return
            if(not self.done):
                if(len(self.filelist) == 0):
                    for x in os.listdir(self.filename):
                        f = os.path.join(self.filename, x)

                        if os.path.isfile(f) and (f[-3:-1] == 'pd' or f[-3:-1] == 'tx'):
                            temp += "\n"+f
                            self.filelist.append(f)

                    if(self.isCsv):
                        self.file = open('data'+str(time.time())+'.csv', "a")

                if(len(self.filelist) != self.fcount):

                    self.process1 = Process(
                        target=self.process, args=(self.filelist[self.fcount], self.proc, False))
                    self.process1.start()

                    self.root.after(250, self.control)
                else:
                    self.filelist = []
                    self.txtbox.delete("1.0", "end")
                    if(self.isCsv):
                        self.txtbox.insert(
                            "1.0", "\n\n\n\t\t\t A New CSV File Is Created...")
                        self.file.close()
        else:

            if(self.process1 != 9512):

                self.count += 1
                self.count %= 8
                self.txtbox.delete("1.0", "end")
                self.txtbox.insert(
                    "1.0", "\n\n\n\n\n\n\n\n\n\n\n \t\t\t\t\t"+steps[self.count]+" Processing "+steps[self.count])

                self.root.after(250, self.control)

                if(not self.process1.is_alive()):
                    self.done = True

                return
            if(not self.done):
                self.process1 = Process(
                    target=self.process, args=(self.filename, self.proc, True))
                self.process1.start()

                self.root.after(250, self.control)

    def show_intro(self):
        self.txtbox.delete("1.0", "end")
        self.txtbox.insert(
            "1.0", self.string)


root = tk.Tk()
c = Controller()
c.root = root
c.string = "\t\t\t\t **Welcome to the SGD Classifier**\n\n  *At Glance*\n\n - The idea is to implement the Sustainalbe Develepment Goals Classifiers using the Machine Learning\n\n - It is Just a GUI Wrap UP for a SVM based Machine Learning Model \n\n - The input can either be .txt format or.pdf format\n\n - This Tool Uses an Multiprocess Module to speed up the exectuion  \n\n - Browse A File Button takes a file as input and spits out the probabilites of SDG Goals \n\n - Browse A Dir Takes a Directory which contains the Company Annual Report and Output them in csv or   excel format\n\n - The Ouput Format is CSV format only\n\n - To start processing click the start button \n\n - All the output is displayed in this text box    "

root.geometry("1000x700")
root.title("Sairam")
tk.Label(root, text='Analyze Output', font='sans 16 normal').place(x=100, y=25)
tk.Button(root, text='Browse A File', width=15,
          font='sans 16 normal', command=c.browseFiles).place(x=750, y=25)

tk.Button(root, text='Browse A Directory', width=15,
          font='sans 16 normal', command=c.browseDir).place(x=450, y=25)

tk.Button(root, text='Start!', width=10,
          font='sans 16 normal', command=c.control, foreground='green').place(x=620, y=125)  # should change this to control as it careates a seperate process
tk.Button(root, text='Instructions', width=10,
          font='sans 16 normal', command=c.show_intro, foreground='blue').place(x=200, y=125)  # should change this to control as it careates a seperate process

c.var = tk.IntVar()
tk.Radiobutton(root, text="CSV", font='sans 16 normal',
               variable=c.var, value=1, command=c.csvorxl,).place(x=100, y=65)

c.txtbox = tk.Text(root, height=27, width=100)
c.txtbox.insert("1.0", c.string)
c.txtbox.place(x=100, y=200)

root.mainloop()

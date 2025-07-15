from ast import GtE
from multiprocessing import context
from ntpath import join
from secrets import choice
#from random import choices
from django.shortcuts import render,get_list_or_404
from django.http import HttpResponse
from . import models

# Create your views here.
def index (request ,):
    return HttpResponse('hey')

def examlistview (request ,):
    exams_list   = models.Exam.objects.all()
    #output = ','.join([exams.ExamName for exams in exams_list])
    context={'exams_list':exams_list}
    return render(request,'ExamsPlatform/examslist.html',context)

def examview (request ,examnum):
    question_list   = models.Question.objects.filter(exam_id=examnum)
    #for q in question_list:
        #models.Question.question_id
    choice_list     = models.Choice.objects.filter(question_id = question_list)  
    context={'question_list':question_list,'choice_list':choice_list}  
    return render(request,'ExamsPlatform/exam.html',context)

def examresultview (request ,examnum):
    question_list   = models.Question.objects.filter(exam_id=examnum)
    #for q in question_list:
        #models.Question.question_id
    choice_list     = models.Choice.objects.filter(question_id = question_list)  
    context={'question_list':question_list,'choice_list':choice_list}  
    return render(request,'ExamsPlatform/result.html',context)